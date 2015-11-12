import bcrypt
import pandas as pd
from databoard.db.model import db, User, Team, Submission, SubmissionFile
from databoard.db.model import NameClashError, MergeTeamError,\
    DuplicateSubmissionError, max_members_per_team
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

import databoard.generic as generic


def date_time_format(date_time):
    return date_time.strftime('%a %Y-%m-%d %H:%M:%S')


######################### Users ###########################

def get_user_teams(user):
    teams = db.session.query(Team).all()
    for team in teams:
        if team in get_team_members(team):
            yield team


def get_n_user_teams(user):
    return len(get_user_teams(user))


def get_hashed_password(plain_text_password):
    """Hash a password for the first time
    (Using bcrypt, the salt is saved into the hash itself)"""
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    """Check hased password. Using bcrypt, the salt is saved into the
    hash itself"""
    return bcrypt.checkpw(plain_text_password, hashed_password)


def create_user(name, password, lastname, firstname, email,
                is_validated=False):
    hashed_password = get_hashed_password(password)
    user = User(name=name, hashed_password=hashed_password,
                lastname=lastname, firstname=firstname, email=email,
                is_validated=is_validated)
    # Creating default team with the same name as the user
    # user is admin of her own team
    team = Team(name=name, admin=user)
    db.session.add(team)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        message = ''
        try:
            db.session.query(User).filter_by(name=name).one()
            message += 'username is already in use'
        except NoResultFound:
            # We only check for team names if username is not in db
            try:
                db.session.query(Team).filter_by(name=name).one()
                db.message += 'username is already in use as a team name'
            except NoResultFound:
                pass
        try:
            db.session.query(User).filter_by(email=email).one()
            if len(message) > 0:
                message += ' and '
            message += 'email is already in use'
        except NoResultFound:
            pass
        if len(message) > 0:
            raise NameClashError(message)
        else:
            raise e
    return user


def validate_user(user):
    user.is_validated = True


def print_users():
    print('***************** List of users ****************')
    for user in db.session.query(User).order_by(User.id_):
        print('{} belongs to teams:'.format(user))
        for team in get_user_teams(user):
            print('\t{}'.format(team))


######################### Teams ###########################


def get_team_members(team):
    if team.initiator is not None:
        # "yield from" in Python 3.3
        for member in get_team_members(team.initiator):
            yield member
        for member in get_team_members(team.acceptor):
            yield member
    else:
        yield team.admin


def get_n_team_members(team):
    return len(list(get_team_members(team)))


def merge_teams(name, initiator_name, acceptor_name):
    initiator = db.session.query(Team).filter_by(name=initiator_name).one()
    acceptor = db.session.query(Team).filter_by(name=acceptor_name).one()
    if not initiator.is_active:
        raise MergeTeamError('Merge initiator is not active')
    if not acceptor.is_active:
        raise MergeTeamError('Merge acceptor is not active')
    # Meaning they are already in another team for the ramp

    # Testing if team size is <= max_members_per_team
    n_members_initiator = get_n_team_members(initiator)
    n_members_acceptor = get_n_team_members(acceptor)
    n_members_new = n_members_initiator + n_members_acceptor
    if n_members_new > max_members_per_team:
        raise MergeTeamError(
            'Too big team: new team would be of size {}, the max is {}'.format(
                n_members_new, max_members_per_team))

    members_initiator = get_team_members(initiator)
    members_acceptor = get_team_members(acceptor)

    # Testing if team (same members) exists under a different name. If the
    # name is the same, we break. If the loop goes through, we add new team.
    members_set = set(members_initiator).union(set(members_acceptor))
    for team in db.session.query(Team):
        if members_set == set(get_team_members(team)):
            if name == team.name:
                break  # ok, but don't add new team, just set them to inactive
            raise MergeTeamError(
                'Team exists with the same members, team name = {}'.format(
                    team.name))
    else:
        team = Team(name=name, admin=initiator.admin,
                    initiator=initiator, acceptor=acceptor)
        db.session.add(team)
    initiator.is_active = False
    acceptor.is_active = False
    try:
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        try:
            db.session.query(Team).filter_by(name=name).one()
            raise NameClashError('team name is already in use')
        except NoResultFound:
            raise e
    return team


def print_active_teams():
    print('***************** List of active teams ****************')
    for team in db.session.query(Team).filter(Team.is_active):
        print('{} members:'.format(team))
        for member in get_team_members(team):
            print('\t{}'.format(member))


######################### Teams ###########################


def get_submissions():
    return db.session.query(Submission).all()


def make_submission(team_name, name, f_name_list):
    team = db.session.query(Team).filter_by(name=team_name).one()
    submission = db.session.query(Submission).filter_by(
        name=name, team=team).one_or_none()
    if submission is None:
        submission = Submission(name=name, team=team)
        for f_name in f_name_list:
            submission_file = SubmissionFile(
                name=f_name, submission=submission)
            db.session.add(submission_file)
        db.session.add(submission)
    else:
        # We allow resubmit for new or failing submissions
        if submission.state == 'new' or 'error' in submission.state:
            submission.state = 'new'
            # Updating existing files or adding new if not in list
            for f_name in f_name_list:
                submission_file = db.session.query(SubmissionFile).filter_by(
                    name=f_name, submission=submission).one_or_none()
                if submission_file is None:
                    submission_file = SubmissionFile(
                        name=f_name, submission=submission)
                    db.session.add(submission_file)
                # else copy the file should be there
                # right now we don't delete files that were not resubmitted,
                # allowing partial resubmission
        else:
            raise DuplicateSubmissionError(
                'Submission "{}" of team "{}" exists already'.format(
                    name, team_name))

    # We should copy files here
    db.session.commit()
    print submission
    return submission


def get_public_leaderboard():
    """
    Returns
    -------
    leaderboard_html : html string
    """

    # We can't query on non-hybrid properties like Submission.name_with_link,
    # so first we make the join then we extract the class members,
    # including @property members (that can't be compiled into
    # SQL queries)
    submissions_teams = db.session.query(Submission, Team).filter(
        Team.id_ == Submission.team_id).filter(
        Submission.is_public_leaderboard).all()
    columns = ['team',
               'submission',
               'score',
               'contributivity',
               'train time',
               'test time',
               'submitted at (UTC)']
    leaderboard_dict_list = [
        {column: value for column, value in zip(
            columns, [team.name,
                      submission.name_with_link,
                      submission.valid_score,
                      submission.contributivity,
                      submission.train_time,
                      submission.test_time,
                      date_time_format(submission.submission_timestamp)])}
        for submission, team in submissions_teams
    ]
    leaderboard_df = pd.DataFrame(leaderboard_dict_list, columns=columns)
    html_params = dict(
        escape=False,
        index=False,
        max_cols=None,
        max_rows=None,
        justify='left',
        classes=['ui', 'blue', 'celled', 'table', 'sortable']
    )
    leaderboard_html = leaderboard_df.to_html(**html_params)
    return leaderboard_html


def set_train_times(submissions):
    """Computes train times (in second) for submissions in submissions
    and sets them in the db.

    Parameters
    ----------
    submissions : list of Submission
        The submissions to score.

    """
    cv_hash_list = generic.get_cv_hash_list()
    n_folds = len(cv_hash_list)

    for submission in submissions:
        train_time = 0.0
        for cv_hash in cv_hash_list:
            _, submission_path = submission.get_paths()
            with open(generic.get_train_time_f_name(
                    submission_path, cv_hash), 'r') as f:
                train_time += abs(float(f.read()))
        train_time = int(round(train_time / n_folds))
        #submission.train_time = train_time
        #submission.train_state = 'scored'
        setattr(submission, 'train_time', train_time)
        submission.state = 'train_scored'
    db.session.commit()


def set_test_times(submissions):
    """Computes test times (in second) for submissions in submissions
    and sets them in the db.

    Parameters
    ----------
    submissions : list of Submission
        The submissions to score.

    """
    cv_hash_list = generic.get_cv_hash_list()
    n_folds = len(cv_hash_list)

    for submission in submissions:
        test_time = 0.0
        for cv_hash in cv_hash_list:
            _, submission_path = submission.get_submission_path()
            with open(generic.get_test_time_f_name(
                    submission_path, cv_hash), 'r') as f:
                test_time += abs(float(f.read()))
        submission.test_time = round(test_time / n_folds)
        submission.test_state = 'scored'
    db.session.commit()


def run_submissions(before_state, after_state, error_state, doing, method):
    """The master method that runs different pipelines (train+valid,
    train+valid+test, test).

    Parameters
    ----------
    submissions : list of Submission
        The list of the models that should be run.
    infinitive, past_participle, gerund : three forms of the action naming
        to be run. Like train, trained, training. Besides message strings,
        past_participle is used for the final state of a successful run
        (trained, tested)
    error_state : the state we get in after an unsuccesful run. The error
        message is saved in <error_state>.txt, to be rendered on the web site
    method : the method to be run (train_and_valid_on_fold,
        train_valid_and_test_on_fold, test_on_fold)
    """
    submissions = db.session.query(Submission).filter(
        Submission.state == before_state).filter(
        Submission.is_valid).all()

    generic.logger.info("Reading data")
    X_train, y_train = specific.get_train_data()
    cv = specific.get_cv(y_train)

    for idx, model_df in models_df.iterrows():
        if model_df['state'] in ["ignore"]:
            continue

        full_model_path = generic.get_full_model_path(idx, model_df)

        generic.logger.info("{} : {}/{}".format(
            str.capitalize(gerund), model_df['team'], model_df['model']))

        try:
            run_on_folds(
                method, full_model_path, cv, team=model_df["team"], tag=model_df["model"])
            # failed_models.drop(idx, axis=0, inplace=True)
            orig_models_df.loc[idx, 'state'] = past_participle
        except Exception, e:
            orig_models_df.loc[idx, 'state'] = error_state
            if hasattr(e, "traceback"):
                msg = str(e.traceback)
            else:
                msg = repr(e)
            generic.logger.error("{} failed with exception: \n{}".format(
                str.capitalize(gerund), msg))

            # TODO: put the error in the database instead of a file
            # Keep the model folder clean.
            with open(generic.get_f_name(full_model_path, '.', error_state, "txt"), 'w') as f:
                error_msg = msg
                cut_exception_text = error_msg.rfind('--->')
                if cut_exception_text > 0:
                    error_msg = error_msg[cut_exception_text:]
                f.write("{}".format(error_msg))


def train_and_valid_models(orig_models_df):
    run_models(orig_models_df, "train", "trained", "training", "error",
               train_and_valid_on_fold)


def train_valid_and_test_submissions(orig_models_df):
    run_models(orig_models_df, "train/test", "tested", "training/testing", "error",
               train_valid_and_test_on_fold)


def test_submissions(orig_models_df):
    run_models(orig_models_df, "test", "tested", "testing", "test_error",
               test_on_fold)


def check_models(orig_models_df):
    run_models(orig_models_df, "check", "new", "checking", "error",
               check_on_fold)


def print_submissions():
    print('***************** List of submissions ****************')
    for submission in db.session.query(Submission).order_by(
            Submission.id_):
        print submission
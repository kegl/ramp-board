# Author: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
# License: BSD 3 clause

import os
import sys
import git
import glob
import shutil
import logging
import hashlib 
import numpy as np
import pandas as pd

from flask_mail import Mail
from flask_mail import Message
from contextlib import contextmanager

from databoard import app
from .model import shelve_database, columns, ModelState
from .specific import hackaton_title
from .config_databoard import repos_path, root_path, tag_len_limit, notification_recipients, server_name


logger = logging.getLogger('databoard')

def send_mail_notif(submissions):
    with app.app_context():
        mail = Mail(app)

        logger.info('Sending notification email to: {}'.format(', '.join(notification_recipients)))
        msg = Message('New submissions in the ' + hackaton_title + ' hackaton', 
            reply_to='djalel.benbouzid@gmail.com')

        msg.recipients = notification_recipients

        body_message = '<b>Dataset</b>: {}<br/>'.format(hackaton_title)
        body_message += '<b>Server</b>: {}<br/>'.format(server_name)

        body_message += 'New submissions: <br/><ul>'
        for team, tag in submissions:
            body_message += '<li><b>{}</b>: {}</li>'.format(team, tag)
        body_message += '</ul>'
        msg.html = body_message

        mail.send(msg)


def copy_git_tree(tree, dest_folder):
    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)
    for file_elem in tree.blobs:
        with open(os.path.join(dest_folder, file_elem.name), 'w') as f:
            shutil.copyfileobj(file_elem.data_stream, f)
    for tree_elem in tree.trees:
        copy_git_tree(tree_elem, os.path.join(dest_folder, tree_elem.name))


@contextmanager  
def changedir(dir_name):
    current_dir = os.getcwd()
    try:
        os.chdir(dir_name)
        yield
    except Exception as e:
        logger.error(e) 
    finally:
        os.chdir(current_dir)


def fetch_models():
    base_path = repos_path
    repo_paths = sorted(glob.glob(os.path.join(base_path, '*')))

    submissions_path = os.path.join(root_path, 'models')

    if not os.path.exists(submissions_path):
        os.mkdir(submissions_path)

    new_submissions = set()  # a set of submission hashes

    # create the database if it doesn't exist
    with shelve_database() as db:
        if 'models' not in db:
            db['models'] = pd.DataFrame(columns=columns)
        models = db['models']
        old_submissions = set(models.index)
        old_failed_submissions = set(models[models['state'] == 'error'].index)

    for repo_path in repo_paths:

        logger.debug(repo_path)

        if not os.path.isdir(repo_path):
            continue

        team_name = os.path.basename(repo_path)
        repo = git.Repo(repo_path)

        try:
            repo.remotes.origin.pull()
        except:
            logger.error('Unable to pull from repo. Possibly no connexion.')

        repo_path = os.path.join(submissions_path, team_name)
        if not os.path.exists(repo_path):
            os.mkdir(repo_path)
        open(os.path.join(repo_path, '__init__.py'), 'a').close()

        if len(repo.tags) == 0:
            logger.debug('No tag found for %s' % team_name)

        for t in repo.tags:
            try:
                tag_name = t.name

                # will serve for the dataframe index
                sha_hasher = hashlib.sha1()
                sha_hasher.update(team_name)
                sha_hasher.update(tag_name)
                tag_name_alias = 'm{}'.format(sha_hasher.hexdigest())

                model_path = os.path.join(repo_path, tag_name_alias)

                with shelve_database() as db:

                    # skip if the model is trained, otherwise, replace the entry with a new one
                    if tag_name_alias in db['models'].index:
                        if db['models'].loc[tag_name_alias, 'state'] == 'trained':
                            continue
                        else:
                            db['models'].drop(tag_name_alias, inplace=True)

                    new_submissions.add(tag_name_alias)

                    # recursively copy the model files
                    copy_git_tree(t.object.tree, model_path)
                    open(os.path.join(model_path, '__init__.py'), 'a').close()

                    commit_time = t.commit.committed_date
                    relative_path = os.path.join(team_name, tag_name_alias)

                    # listing the model files
                    file_listing = [f for f in os.listdir(model_path) if os.path.isfile(os.path.join(model_path, f))]

                    # filtering useless files
                    file_listing = filter(lambda f: not f.startswith('__'), file_listing)
                    file_listing = filter(lambda f: not f.endswith('.pyc'), file_listing)
                    file_listing = filter(lambda f: not f.endswith('.csv'), file_listing)
                    file_listing = filter(lambda f: not f.endswith('error.txt'), file_listing)
                    
                    # prepre a dataframe for the concatnation 
                    new_entry = pd.DataFrame({
                        'team': team_name, 
                        'model': tag_name, 
                        'timestamp': t.commit.committed_date, 
                        'path': os.path.join(team_name, tag_name_alias),
                        'state': "new",
                        # 'listing': file_listing,
                    }, index=[tag_name_alias])

                    # set a list into a cell
                    new_entry.set_value(tag_name_alias, 'listing', file_listing)
                    db['models'] = db['models'].append(new_entry)

            except Exception, e:
                logger.error("%s" % e)


    # remove the failed submissions that have been deleted
    removed_failed_submissions = old_failed_submissions - set(new_submissions)
    with shelve_database() as db:
        db['models'].drop(removed_failed_submissions, inplace=True)

    # read-only
    # with shelve_database('r') as db:
    with shelve_database() as db:
        df = db['models']
        logger.debug(df)
        really_new_submissions = df.loc[new_submissions - old_submissions][['team', 'model']].values

    if len(really_new_submissions):
        try:
            send_mail_notif(really_new_submissions)
        except:
            logger.error('Unable to send email notifications for new models.')
    else:
        logger.debug('No new submission.')
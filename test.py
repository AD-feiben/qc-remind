from main import task
import config


if __name__ == '__main__':
    if config.mail_host == '':
        raise Exception('mail_host is empty')
    if config.mail_user == '':
        raise Exception('mail_user is empty')
    if config.mail_pass == '':
        raise Exception('mail_pass is empty')
    task()

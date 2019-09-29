from main import task
import config


if __name__ == '__main__':
    if config.Mail_host == '':
        raise Exception('mail_host is empty')
    if config.Mail_user == '':
        raise Exception('mail_user is empty')
    if config.Mail_pass == '':
        raise Exception('mail_pass is empty')
    task()

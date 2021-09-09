from riotwatcher import LolWatcher
from requests.exceptions import HTTPError
from datetime import datetime
from pyfcm import FCMNotification
import config
import time

print('Registering API Keys')
lol_watcher = LolWatcher(config.RIOT_API_KEY)
push_service = FCMNotification(config.FCM_API_KEY)


def to_timespan(delta):
    delta = delta.total_seconds()
    m = int(delta / 60)
    if m < 10:
        m = '0' + str(m)
    s = int(delta % 60)
    if s < 10:
        s = '0' + str(s)
    return '{}:{}'.format(m, s)


def send_message(body, title):
    result = push_service.notify_topic_subscribers(topic_name="alert", data_message={
        "body": body,
        "title": title
    })


def run():
    playerIDs = []
    for name in config.TARGET_PLAYERS:
        try:
            playerIDs.append({
                'data': lol_watcher.summoner.by_name('kr', name),
                'playing': False
            })
        except HTTPError:
            print('Incorrect player name: ' + name)
            return

    print('Start watching...')
    send_message('게임 추적을 시작합니다.', '롤 게임 추적기')
    while True:
        try:
            for player in playerIDs:
                try:
                    spectator = lol_watcher.spectator.by_summoner('kr', player['data']['id'])
                    if not player['playing']:
                        player['playing'] = True
                        start_time = datetime.fromtimestamp(spectator['gameStartTime'] / 1000)
                        message = '{}님이 게임중입니다! 시작 시각: {}, 진행 시간: {}'.format(player['data']['name'],
                                                                            start_time.strftime('%H:%M:%S'),
                                                                            to_timespan(datetime.now() - start_time))
                        print(message)
                        send_message(message, '롤 게임 추적기')
                except HTTPError:
                    player['playing'] = False
                    pass
        except BaseException as error:
            print('Unexpected exception: {}'.format(error))
        time.sleep(config.DETECT_PERIOD_SEC)


run()

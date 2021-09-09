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
    if delta > 60 * 60 * 5:
        return '알 수 없음'

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
    send_message('게임 추적을 시작합니다. \n추적 대상: ' + ", ".join(config.TARGET_PLAYERS), '롤 게임 추적기')
    time_phase = -1

    while True:
        time_phase += 1
        try:
            for player in playerIDs:
                if not player['playing'] and time_phase % 4 != 0:
                    continue
                try:
                    spectator = lol_watcher.spectator.by_summoner('kr', player['data']['id'])
                    if not player['playing']:
                        player['playing'] = True
                        start_time = datetime.fromtimestamp(spectator['gameStartTime'] / 1000)
                        message = '{}님이 게임중입니다! (게임 시간: {})'.format(player['data']['name'], to_timespan(datetime.now() - start_time))
                        print(message)
                        send_message(message, '롤 게임 추적기')
                except HTTPError:
                    if player['playing']:
                        player['playing'] = False
                        message = player['data']['name'] + '님 게임이 끝났습니다.'
                        print(message)
                        send_message(message, '롤 게임 추적기')
                    pass
        except BaseException as error:
            print('Unexpected exception: {}'.format(error))
        time.sleep(config.DETECT_PERIOD_SEC / config.TIMES_OF_DETECT_PERIOD_ON_PLAYING)

run()

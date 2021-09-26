from riotwatcher import LolWatcher
from requests.exceptions import HTTPError
from datetime import datetime
from pyfcm import FCMNotification
import config
import time

print('Registering API Keys')
lol_watcher = LolWatcher(config.RIOT_API_KEY)
push_service = FCMNotification(config.FCM_API_KEY)
time_phase = -1


def calculate_playing_time(start_timestamp):
    now = datetime.now()
    start_time = datetime.fromtimestamp(start_timestamp / 1000)
    if start_timestamp == 0 or now < start_time:
        return '00:00'

    return (now - start_time).total_seconds()


def get_formatted_playing_time(start_timestamp):
    delta = calculate_playing_time(start_timestamp)
    m = int(delta / 60)
    if m < 10:
        m = '0' + str(m)
    s = int(delta % 60)
    if s < 10:
        s = '0' + str(s)
    return '{}:{}'.format(m, s)


def send_message(body, title):
    push_service.notify_topic_subscribers(topic_name="alert", data_message={
        "body": body,
        "title": title
    })


def info(message):
    print("Info[t=" + str(time_phase) + "]: " + message)


def debug(message):
    if config.USE_DEBUG_LOG:
        print("Debug[t=" + str(time_phase) + "]: " + message)


def is_in_time(start_timestamp, duration):
    delta = calculate_playing_time(start_timestamp)
    m = int(delta / 60)
    return m <= duration


def run():
    global time_phase
    playerIDs = []
    print('Loading player hashes...')
    for name in config.TARGET_PLAYERS:
        try:
            playerIDs.append({
                'data': lol_watcher.summoner.by_name('kr', name),
                'playing': False,
                'isFirst': True
            })
        except HTTPError:
            print('Incorrect player name: ' + name)
            return

    print('Start watching')
    send_message('게임 추적을 시작합니다. \n추적 대상: ' + ", ".join(config.TARGET_PLAYERS), '롤 게임 추적기')

    while True:
        time_phase += 1
        try:
            for player in playerIDs:
                if not player['playing'] and time_phase % config.TIMES_OF_DETECT_PERIOD_ON_PLAYING != 0:
                    continue
                try:
                    debug("Check " + player['data']['name'])
                    spectator = lol_watcher.spectator.by_summoner('kr', player['data']['id'])
                    debug(str(spectator))
                    if not player['playing'] and (player['isFirst'] or is_in_time(spectator['gameStartTime'], config.FILTERING_GAME_TIME_MIN)):
                        player['playing'] = True
                        player['isFirst'] = False
                        start_time = get_formatted_playing_time(spectator['gameStartTime'])
                        message = '{}님이 게임중입니다! (게임 시간: {})'.format(player['data']['name'], start_time)
                        info(message)
                        send_message(message, '롤 게임 추적기')
                except HTTPError as error:
                    debug(str(error))
                    if player['playing']:
                        player['playing'] = False
                        message = player['data']['name'] + '님 게임이 끝났습니다.'
                        info(message)
                        send_message(message, '롤 게임 추적기')
        except BaseException as error:
            print('Unexpected exception: {}'.format(error))
        time.sleep(config.DETECT_PERIOD_SEC / config.TIMES_OF_DETECT_PERIOD_ON_PLAYING)


run()

import utils
import jps
import json


def main(host='smilerobotics.com'):
    try:
        sub = jps.Subscriber('sound', host=host)
        sound_file_dict = {'chime': 'se_maoudamashii_chime05.wav',
                           'pico': 'se_maoudamashii_onepoint28.wav',
                           'piro': 'se_maoudamashii_onepoint24.wav',
                           'tired': 'se_maoudamashii_chime05.wav',
                           'shasha': 'se_maoudamashii_magical30.wav',
                       }
        for msg in sub:
            sound_command = json.loads(msg)
            if 'sound' in sound_command:
                sound = sound_command['sound']
                utils.play_sound(sound_file_dict[sound]).wait()
                if 'speak' in sound_command:
                    text = sound_command['speak']
                    utils.speak(text).wait()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main(host='smilerobotics.com')


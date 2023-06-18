import nls
import threading
import aliyun_utils
import proj_utils

# print("ACCESS_TOKEN: {}, ACCESS_APPKEY: {}".format(m_utils.ACCESS_TOKEN, m_utils.ACCESS_APPKEY))


class Tts:
    def __init__(self, tid, file):
        self.__th = threading.Thread(target=self.run)
        self.__id = tid
        self.__file = file
        self.flag = False

    def start(self, text):
        self.__text = text
        self.__f = open(self.__file, "wb")
        self.__th.start()

    def wait(self):
        while (self.flag == False):
            pass

    def on_metainfo(self, message, *args):
        # print("on_metainfo message=>{}".format(message))
        pass

    def on_error(self, message, *args):
        # print("on_error args=>{}".format(args))
        pass

    def on_close(self, *args):
        print("on_close: args=>{}".format(args))
        try:
            self.__f.close()
        except Exception as e:
            print("close file failed since:", e)

    def on_data(self, data, *args):
        try:
            self.__f.write(data)
        except Exception as e:
            print("write data failed:", e)

    def on_completed(self, message, *args):
        print("on_completed:args=>{} message=>{}".format(args, message))
        self.flag = True

    def run(self):
        print("thread:{} start..".format(self.__id))
        tts = nls.NlsSpeechSynthesizer(
            url=aliyun_utils.URL,
            token=aliyun_utils.ACCESS_TOKEN,
            appkey=aliyun_utils.ACCESS_APPKEY,
            on_metainfo=self.on_metainfo,
            on_data=self.on_data,
            on_completed=self.on_completed,
            on_error=self.on_error,
            on_close=self.on_close,
            callback_args=[self.__id]
        )

        print("{}: session start".format(self.__id))
        r = tts.start(self.__text, voice="zhimiao_emo",
                      ex={'enable_subtitle': True},
                      aformat="wav", volume=100)
        print("{}: tts done with result:{}".format(self.__id, r))

# Usage
# t = Tts(tid="thread id", file=filepath)
# t.start(text)

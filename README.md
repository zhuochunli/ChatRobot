# ChatRobot
This is a smart stock query robot which you can ask on Wechat

这是一个可以帮你查询股票信息的机器人，你可以通过三种方式输入信息：

1、静态输入，提前输入好至数组中。

2、循环动态输入，每次在console中输入。

3、扫码登陆微信，并通过微信加好友后，发送信息问询。

三种输入方式对应的函数在ChatRobot.py中均已注释，可根据需求自由选择，当前默认为微信方式。

输入hello或bye类似意图的句子来开始或结束聊天查询。

必须用手机号登陆才能查询，手机号为6位数字。

本机器人采用iexcloud的免费股票查询API帮助您查询，你可询问某公司的股票某一参数，如：
What's the latestPrice of Tesla？
它会将这一参数单独提出来返回给您。

注：目前因为各公司名和公司股票名（symbol）不对应，且interpret函数中spacy的实体识别只能把公司识别为ORG。所以现在只手动添加了几个公司和其股票名的映射，若有全部公司名的股票名映射表，即可实现自由查询各个公司股票信息。

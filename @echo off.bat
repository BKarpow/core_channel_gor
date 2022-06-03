@echo off

call %~dp0core_channel_gor\Scripts\activate
cd %~dp0core_channel_gor\
set TELEGRAM_TOKEN=
set CHAT_ID=@horodysche_channel
set W_URL=https://api.openweathermap.org/data/2.5/onecall
set W_API_KEY=
set JSON_SOURCE_URL=https://tg.i-c-a.su/json/air_alert_ua?limit=100
set AIR_ALERT_DB=air_alerts.db
set TIME_COMMENDANT_START=23:00
set TIME_COMMENDANT_END=05:00
set CRON_URL=https://karpow.pp.ua/actions/gor_gromada_news_tg_bot/airCron.php
set CRON_TIMEOUT=45
set NAME_RSS_DB=rss_news.db
set RSS_XML_SOURCE=https://gromada.org.ua/rss/104208/
python main.py -c all
pause
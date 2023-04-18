from com.jobs.task_synch_hr import synchronize_hr_data_job
from com.jobs.task_reinsurance_remind import reinsurance_remind_job
from com.jobs.task_borrow_remind import borrow_remind_job
from com.jobs.task_asset_in_remind import asset_in_remind_job
# from pm.jobs.task_synch_gsr import synchronize_gsr_data_job
# from pm.jobs.task_demo import synch_demo
'''
任务清单
注意时间顺序问题：后面的时间早于前面的则不会执行，如：
synchronize_hr_data_job设定执行时间为20:30，send_email_job设定为8:00
send_email_job则不会执行
'''
jobs = [
    # 每天凌晨1点执行
    {
        "id": "synchronize_hr_data_job",
        "func": synchronize_hr_data_job,
        #"args": (, ),
        "trigger": "cron",
        "hour": 1,
        "minute": 0
    },
    # 每周一上午7点5分执行-维保到期提醒
    {
        "id": "reinsurance_remind_job",
        "func": reinsurance_remind_job,
        #"args": (, ),
        "trigger": "cron",
        "day_of_week": 0,   # 一周有7天，用0-6表示，比如指定0-3，则表示周一到周四。不指定则为7天，也可以用mon,tue,wed,thu,fri,sat,sun表示
        "hour": 7,
        "minute": 5
    },
    # 每天上午7点10分执行-借用到期提醒
    {
        "id": "borrow_remind_job",
        "func": borrow_remind_job,
        #"args": (, ),
        "trigger": "cron",
        "hour": 7,
        "minute": 10
    },
    # 每天上午7点15分执行-预计搬入到期提醒
    {
        "id": "asset_in_remind_job",
        "func": asset_in_remind_job,
        #"args": (, ),
        "trigger": "cron",
        "hour": 7,
        "minute": 15
    }
]
'''
每300秒执行一次
{
    "id": "synch_demo",
    "func": synch_demo,
    "args": (10, 20),
    "trigger": "interval",
    "seconds": 300
}'''
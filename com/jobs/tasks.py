from com.jobs.task_synch_hr import synchronize_hr_data_job
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
    }
]
'''
每300秒分钟执行一次
{
    "id": "synch_demo",
    "func": synch_demo,
    "args": (10, 20),
    "trigger": "interval",
    "seconds": 5000
}'''
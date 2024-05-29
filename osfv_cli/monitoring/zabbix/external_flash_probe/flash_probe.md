# How To implement This script?

1. Move `flash_probe.sh`, `flash_read.sh`, `flash_write.sh` to external script location.

- By default it is:

```C
/usr/lib/zabbix/externalscripts
```

2. Create Crontab job.

```C
crontab -e
```

> The script runs every 30 minutes between 4:00 AM and 10:00 PM, Monday to Friday.

```C
*/30 4-22 * * 1-5 /usr/lib/zabbix/externalscripts/flash_probe.sh
```

## Create Template

1. Navigate to **Configuration** > **Templates**.
2. Click **Create template** in top right.
- Specify the name, group and other information if needed.

## Create Items

1. First item.
- Change type to **External check**.
- Set Key to `flash_read.sh[{HOST.IP}]`.
- Set update interval to 5m.

2. Second item.
- Change type to **External check**.
- Set Key to `flash_write.sh[{HOST.IP}]`.
- Set **update interval** to **5m**.

## Create Triggers

1. First trigger.
- Severity: **High**
- Expression: `max(/Flash probe/flash_read.sh[{HOST.IP}],15m)=2`

2. Second trigger.
- Severity: **Information**
- Expression: `max(/Flash probe/flash_read.sh[{HOST.IP}],25m)=1`

## Link Hosts to the template

1. Mass update
- Go to **Hosts**.
- Check the boxes next to the desired hosts.
- Scroll to the bottom and click **Mass update**.
    + Select **Link templates**.
    + Choose **Link**.
    + Enter your template name.
    + Press **Update**.

2. Single update.
- Go to **Hosts**.
    + Open desired **Host**.
    + Add your Template under Templates.
    + Press **Update**.

## Testing

1. Test manually.
- login as **zabbix** user and go to the script location.
- run your script as zabbix.

> You can incorporate Zabbix macros into your command, `./script.sh '192.168.10.0'`.

2. Test in zabbix web interface.
- Go to your item location.
- If you are using external checks, **Test** option should be available.
- Check if you Macros give proper data to your script.
- Press **Get value and test**.

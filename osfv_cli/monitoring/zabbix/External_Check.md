# External Check Zabbix

This is a brief guide on setting up external checks in Zabbix.
You can find example scripts in this folder.

## Preparation

1. Make sure your script is in

```C
/usr/lib/zabbix/externalscripts
```

> The default location can be changed in `/etc/zabbix/zabbix_server.conf`
> by editing `ExternalScripts=/usr/lib/zabbix/externalscripts`

**Ensure that you have only one tab open when creating anything in Zabbix (items/triggers/hosts).**

> It's likely that the last used tab is overwriting session data.

## Create the item in Zabbix

> Item is a tool that gathers data from device, system or external script

1. Navigate to **Configuration** > **Hosts**.
1. Go to the **Items** next to the host you want to monitor.
1. Click **Create item** in top right.
- Change Type to **External check**.
- As key use your script name together with desired **Macro**, for example `script.sh[{HOST.IP}]`.

> [External Checks](https://www.zabbix.com/documentation/current/en/manual/config/items/itemtypes/external)
> [List of macros](https://www.zabbix.com/documentation/current/en/manual/appendix/macros/supported_by_location#host-inventory)

## Create the trigger

> Trigger is a rule that watches for specific events, like high CPU usage.

1. Navigate to **Configuration** > **Hosts**.
1. Go to the **Triggers** next to the host with the item you want to monitor.
1. Click **Create trigger** in top right.
- Severity: Select as needed.
- Expression: press Add
    + Item: Select the item for which you want to create a trigger.
    + Function: Defines how your trigger will be activated.
    + Result: Actual rule of activation.

## Testing

1. Test manually.
- login as **zabbix** user and go to the script location.
- run your script as zabbix.

1. Test in zabbix web interface.
- Go to your item location.
- If you are using external checks, **Test** option should be available.
- Check if you Macros give proper data to your script.
- Press **Get value and test**.

1. Common problems.
- Timeout: you can change Timeout value in `/etc/zabbix/zabbix_server.conf`
- Make sure all necesery files and commands are accessible for zabbix user.
- If you find something else, please update the file.

## Templates

1. Navigate to **Configuration** > **Templates**.
1. Click **Create template** in top right.
- Specify the name, group and other information if needed.
1. Add **items**, **trigger** and **macros** if needed.
1. Link the template to **Hosts**
1. Mass update
- Go to **Hosts**.
- Check the boxes next to the desired hosts.
- Scroll to the bottom and click **Mass update**.
    + Select **Link templates**.
    + Choose **Link**.
    + Enter your template name.
    + Press **Update**.

1. Single update
- Go to **Hosts**.
    + Open desired **Host**.
    + Add your Template under Templates.
    + Press **Update**.

# External Check Zabbix

This is a brief guide on setting up external checks in Zabbix.
You can find example scripts in this folder.

## Preparation
1. Make sure your script is in 
```
/usr/lib/zabbix/externalscripts 
```
> The default location of externalscripts can be changed in `/etc/zabbix/zabbix_server.conf` by editing `ExternalScripts=/usr/lib/zabbix/externalscripts` (make sure to remove #)

**Ensure that you have only one tab open when creating anything in Zabbix (items/triggers/hosts).**
> It's likely that the last used tab is overwriting session data.



## Create the item in Zabbix
> Item is a tool that gathers data from device, system or external script
2. Navigate to **Configuration** > **Hosts**.
2. Go to the **Items** next to the host you want to monitor.
2. Click **Create item** in top right.
	- Change Type to **External check**.
	- As key use your script name together with desired **Macro**, for example `script.sh[{HOST.IP}]`.
		+ You can combine multiple Macros `script.sh[{HOST.DESCRIPTION},{HOST.ID},{HOST.CONN}]`.
	

[list of macros](https://www.zabbix.com/documentation/current/en/manual/appendix/macros/supported_by_location#host-inventory)

## Create the trigger
> Trigger is a rule that watches for specific events, like high CPU usage.
3. Navigate to **Configuration** > **Hosts**.
3. Go to the **Triggers** next to the host with the item you want to monitor.
3. Click **Create trigger** in top right.
	- Severity: Select as needed.
	- Expression: press Add
		+ Item: Select the item for which you want to create a trigger.
		+ Function: Defines how your trigger will be activated.
		+ Result: Actual rule of activation.
> If your script returns numeric values directly and/or you don't won't to calculate the average result, simply use `last()` function

## Testing
4. Test manually.
- login as **zabbix** user and go to the script location.
- run your script as zabbix.
> You can directly incorporate information from Zabbix macros into your command, such as ./script.sh '192.168.10.0'.

4. Test in zabbix web interface.
- Go to your item location. 
- If you are using external checks, **Test** option should be available.
	+ Check if you Macros give proper data to your script.
	+ Press **Get value and test**.

4. Common problems.
- Timeout: you can change (not VM)Timeout(and TrapperTimeout if needed) settings in /etc/zabbix/zabbix_server.conf
- Make sure all necesery files and commands are accessible for zabbix user.
- If you find something else, please update the file.

## Templates
5. Navigate to **Configuration** > **Templates**. 
5. Click **Create template** in top right.
	- Specify the name, group and other information if needed.
5. Add **items**, **trigger** and **macros** if needed.
5. Link the template to **Hosts**
	5. Mass update
		- Go to **Hosts**.
		- Check the boxes next to the desired hosts.
		- Scroll to the bottom and click **Mass update**.
			+ Select **Link templates**.
			+ Choose **Link**.
			+ Enter your template name.
			+ Press **Update**.
 
	5. Single update
		- Open desired **Host**.
		- Add your Template under Templates.
		- Press **Update**.

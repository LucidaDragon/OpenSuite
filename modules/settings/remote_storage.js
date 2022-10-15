const remoteStorage = {
	"initialize": (module) =>
	{
		remoteStorage.key = async (n) =>
		{
			return Object.keys((await (await fetch(`/settings/get_all`, {
				"headers": {
					"Authorization": session.get_token()
				}
			})).json())[module])[n];
		};

		remoteStorage.setItem = async (keyName, keyValue) =>
		{
			await fetch(`/settings/set?module=${encodeURIComponent(module)}&name=${encodeURIComponent(keyName)}`, {
				"method": "POST",
				"headers": {
					"Content-Type": "application/json",
					"Authorization": session.get_token()
				},
				"body": JSON.stringify(keyValue)
			});
		};

		remoteStorage.getItem = async (keyName) =>
		{
			try
			{
				return await (await fetch(`/settings/get?module=${encodeURIComponent(module)}&name=${encodeURIComponent(keyName)}`, {
					"method": "GET",
					"headers": {
						"Authorization": session.get_token()
					}
				})).json();
			}
			catch
			{
				return null;
			}
		};

		remoteStorage.removeItem = async (keyName) =>
		{
			await fetch(`/settings/delete?module=${encodeURIComponent(module)}&name=${encodeURIComponent(keyName)}`, {
				"method": "POST",
				"headers": {
					"Authorization": session.get_token()
				}
			});
		};

		remoteStorage.clear = async () =>
		{
			await fetch(`/settings/clear?module=${encodeURIComponent(module)}`, {
				"method": "POST",
				"headers": {
					"Authorization": session.get_token()
				}
			});
		};
	},
	"key": async (n) =>
	{
		throw "Remote storage must be initialized before calling key.";
	},
	"setItem": async (keyName, keyValue) =>
	{
		throw "Remote storage must be initialized before calling setItem.";
	},
	"getItem": async (keyName) =>
	{
		throw "Remote storage must be initialized before calling getItem.";
	},
	"removeItem": async (keyName) =>
	{
		throw "Remote storage must be initialized before calling removeItem.";
	},
	"clear": async (keyName) =>
	{
		throw "Remote storage must be initialized before calling clear.";
	}
};
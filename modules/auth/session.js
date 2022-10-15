const session = {
	"get_token": function()
	{
		const result = window.sessionStorage.getItem("token");
		
		if (result === null)
		{
			window.location = `/auth/index.html?redirect=${encodeURIComponent(window.location.pathname)}`;
			throw "Authentication is required to retrieve the session token.";
		}
		
		return result;
	}
};

{
	async function validate()
	{
		if (!((await fetch("/auth/ping", {
			"headers": {
				"Authorization": session.get_token()
			}
		})).ok))
		{
			window.sessionStorage.removeItem("token");
			session.get_token()
		};
	}

	setInterval(validate, 60000);
	validate();
}
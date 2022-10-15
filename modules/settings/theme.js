window.addEventListener("DOMContentLoaded", function()
{
	fetch("/settings/theme", {
		"headers": {
			"Authorization": session.get_token()
		}
	}).then(async function(response)
	{
		const style = document.createElement("style");
		style.innerText = await response.text();
		document.head.appendChild(style);
	});
});
window.addEventListener("DOMContentLoaded", async function()
{
	remoteStorage.initialize("weather");

	const weather = await (await fetch("/weather/get", {
		"headers": {
			"Authorization": session.get_token()
		}
	})).json();

	if ((await remoteStorage.getItem("temperature-unit")).toUpperCase() === "C")
	{
		document.getElementById("weather-tempf").style.display = "none";
	}
	else
	{
		document.getElementById("weather-tempc").style.display = "none";
	}

	if (Object.keys(weather).includes("currently"))
	{
		document.getElementById("weather-icon").src = weather.currently["icon-path"];
		document.getElementById("weather-tempc").innerText = (Math.floor(weather.currently["temperature-c"] * 10) / 10) + " \u00B0C"
		document.getElementById("weather-tempf").innerText = (Math.floor(weather.currently["temperature-f"] * 10) / 10) + " \u00B0F"
	}
});
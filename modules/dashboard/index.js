window.addEventListener("DOMContentLoaded", async function()
{
	remoteStorage.initialize("dashboard");
	const style = document.createElement("style");
	style.innerText = `:root { --icon-button-size: ${await remoteStorage.getItem("icon-button-size")}; --icon-center-size: ${await remoteStorage.getItem("icon-center-size")}; }`;
	document.head.appendChild(style);

	const response = await fetch("/dashboard/icons", {
		"headers": {
			"Authorization": session.get_token()
		}
	});
	const module_list = document.getElementById("module-list");

	if (response.ok)
	{
		const icons = await response.json();
		const modules = Object.keys(icons);

		modules.forEach(function(module)
		{
			const entry = document.createElement("button");
			entry.classList.add("module-entry");
			entry.innerHTML = icons[module];
			entry.addEventListener("click", function()
			{
				window.location.pathname = `/${module}/index.html`;
			});

			const spacing = document.createElement("div");
			spacing.classList.add("module-spacing");

			const label = document.createElement("label");
			label.classList.add("module-label");
			if (module.length > 0) label.innerText = module[0].toUpperCase() + module.substring(1);

			entry.appendChild(spacing);
			entry.appendChild(label);

			module_list.appendChild(entry);
		});
	}
});
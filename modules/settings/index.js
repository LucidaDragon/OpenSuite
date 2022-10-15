function create_property_editor(module, name, value)
{
	const property_name = document.createElement("label");
	property_name.classList.add("property-name");
	property_name.innerText = name;

	const property_value = document.createElement("input");
	property_value.setAttribute("data-property-module", module);
	property_value.setAttribute("data-property-name", name);
	property_value.setAttribute("data-original-value", value);
	property_value.classList.add("property-value");
	property_value.value = value;

	return [property_name, property_value];
}

function create_container(text, child_elements)
{
	if (text === undefined) text = "";
	if (child_elements === undefined) child_elements = [];

	const outer = document.createElement("div");
	outer.classList.add("outer-container");
	outer.classList.add("collapsed-outer");

	const toggle_button = document.createElement("button");
	toggle_button.classList.add("container-toggle");
	toggle_button.innerText = text;

	const inner = document.createElement("div");
	inner.classList.add("inner-container");

	toggle_button.addEventListener("click", function()
	{
		if (outer.classList.contains("collapsed-outer"))
		{
			outer.classList.remove("collapsed-outer");
		}
		else
		{
			outer.classList.add("collapsed-outer");
		}
	});

	child_elements.forEach(function(child)
	{
		inner.appendChild(child)
	});

	outer.appendChild(toggle_button);
	outer.appendChild(inner);

	return outer;
}

async function restore(parent)
{
	const settings = (await (await fetch("/settings/get_all", {
		"headers": {
			"Authorization": session.get_token()
		}
	})).json());

	Object.keys(settings).forEach(function(module)
	{
		parent.appendChild(create_container(module[0].toUpperCase() + module.substring(1), Object.keys(settings[module]).map(function(name)
		{
			return create_property_editor(module, name, settings[module][name])
		}).flat(1)));
	});
}

async function save(parent)
{
	const properties = parent.getElementsByClassName("property-value");
	for (let i = 0; i < properties.length; i++)
	{
		const property = properties[i];
		if (property.value !== property.getAttribute("data-original-value"))
		{
			remoteStorage.initialize(property.getAttribute("data-property-module"));
			await remoteStorage.setItem(property.getAttribute("data-property-name"), property.value);
		}
	}

	remoteStorage.initialize("settings");
}

window.addEventListener("load", async function()
{
	await restore(document.getElementById("settings-list"));

	document.getElementById("restore-button").addEventListener("click", async function()
	{
		await restore(document.getElementById("settings-list"));
	});

	document.getElementById("save-button").addEventListener("click", async function()
	{
		await save(document.getElementById("settings-list"));
		window.location.reload();
	})
});
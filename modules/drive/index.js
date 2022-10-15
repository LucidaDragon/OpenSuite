window.addEventListener("DOMContentLoaded", async function()
{
	const current_directory = new URLSearchParams(window.location.search).get("directory");

	document.body.addEventListener("dragover", function(e)
	{
		e.preventDefault();
	});

	async function upload_file(name, buffer)
	{
		return new Promise(async function(resolve, reject)
		{
			const request = new XMLHttpRequest();
			const indicator = await create_progress_indicator(name, function()
			{
				request.abort();
				indicator.remove();
			});
			request.open("POST", `/drive/file?name=${encodeURIComponent(name)}${current_directory === null ? "" : `&parent=${encodeURIComponent(current_directory)}`}`, true);
			request.upload.onprogress = function(e)
			{
				indicator.set_progress((e.loaded * 100) / e.total);
			};
			request.onload = async function(e)
			{
				indicator.remove();
				add_entry_tile(JSON.parse(request.responseText)["file"]);
				resolve({ "ok": true, "file_source": name });
			};
			request.onerror = function(e)
			{
				indicator.remove();
				resolve({ "ok": false, "file_source": name });
			};
			request.setRequestHeader("Content-Type", "application/octet-stream");
			request.setRequestHeader("Content-Length", buffer.size);
			request.setRequestHeader("Authorization", session.get_token());
			request.send(buffer);
		});
	}

	function get_download_path(owner, id)
	{
		return `/drive/file?owner=${encodeURIComponent(owner)}&file=${encodeURIComponent(id)}`;
	}

	function get_download_url(owner, id)
	{
		const port = window.location.port ? `:${window.location.port}` : "";
		return `${window.location.protocol}//${window.location.hostname}${port}${get_download_path(owner, id)}`;
	}

	function download_file(owner, id)
	{
		function encode_utf8(str)
		{
			const codePoints = new Uint16Array(str.length);
			for (let i = 0; i < str.length; i++) codePoints[i] = str.charCodeAt(i);
			return String.fromCharCode(...new Uint8Array(codePoints.buffer));
		}

		document.cookie = `Authorization=${btoa(encode_utf8(session.get_token()))};expires=${new Date(new Date().getTime() + 5000).toUTCString()} ;path=/${window.location.protocol != "http:" ? " ; Secure" : ""}`;
		window.location = get_download_path(owner, id);
	}

	document.body.addEventListener("drop", async function(e)
	{
		e.preventDefault();

		const responses = [];

		if (e.dataTransfer.items)
		{
			for (let i = 0; i < e.dataTransfer.items.length; i++)
			{
				const item = e.dataTransfer.items[i];
				if (item.kind === "file")
				{
					const file = item.getAsFile();
					responses.push(upload_file(file.name, file));
				}
			}
		}
		else
		{
			for (let i = 0; i < e.dataTransfer.files.length; i++)
			{
				const file = e.dataTransfer.files[i];
				responses.push(upload_file(file.name, file));
			}
		}

		const fails = (await Promise.all(responses)).filter(function(response) { return !response.ok; });
		if (fails.length > 0)
		{
			alert(`"${fails.map(function(response) { return response.file_source; }).join("\", \"")}" failed to upload.`);
		}
	});

	remoteStorage.initialize("drive");
	const style = document.createElement("style");
	style.innerText = `:root { --icon-button-size: ${await remoteStorage.getItem("icon-button-size")}; --icon-center-size: ${await remoteStorage.getItem("icon-center-size")}; }`;
	document.head.appendChild(style);

	const file_list = document.getElementById("file-list");

	const remote_elements = {};

	async function get_element(uri)
	{
		let content = null;
		if (Object.keys(remote_elements).includes(uri))
		{
			content = remote_elements[uri];
		}
		else
		{
			content = await (await fetch(uri)).text();
			remote_elements[uri] = content;
		}

		const e = document.createElement("x-element");
		e.innerHTML = content;
		return e.childNodes[0];
	}

	async function create_context_menu(position, items)
	{
		const menus = document.getElementsByClassName("context-menu");
		for (let i = 0; i < menus.length; i++) menus[i].parentElement.removeChild(menus[i]);

		const menu = document.createElement("div");
		menu.classList.add("context-menu");
		menu.style.left = `${position.x}`;
		menu.style.top = `${position.y}`;

		const close_button = document.createElement("button");
		close_button.classList.add("context-menu-close");
		close_button.appendChild(await get_element("/drive/close.svg"));
		close_button.addEventListener("click", function()
		{
			menu.parentElement.removeChild(menu);
		});
		menu.appendChild(close_button);

		Object.keys(items).forEach(function(key)
		{
			const entry = document.createElement("button");
			entry.classList.add("context-menu-item");
			entry.innerText = key;
			entry.addEventListener("click", function() { menu.parentElement.removeChild(menu); items[key](); });
			menu.appendChild(entry);
		});

		document.body.appendChild(menu);
	}

	async function create_progress_indicator(name, on_cancel)
	{
		let stack = document.getElementById("progress-stack");
		if (stack === null)
		{
			stack = document.createElement("div");
			stack.id = "progress-stack";
			document.body.appendChild(stack);
		}

		const label = document.createElement("label");
		label.classList.add("progress-label");
		label.innerText = name;
		const progress_outer = document.createElement("div");
		progress_outer.classList.add("progress-outer");
		const progress_inner = document.createElement("div");
		progress_inner.classList.add("progress-inner");
		const progress_cancel = document.createElement("button");
		progress_cancel.classList.add("progress-cancel");
		progress_cancel.appendChild(await get_element("/drive/close.svg"));

		progress_outer.appendChild(progress_inner);
		stack.appendChild(label);
		stack.appendChild(progress_outer);
		if (on_cancel) stack.appendChild(progress_cancel);

		const indicator = {
			"set_progress": function(percent) { progress_inner.style.width = `${percent}%`; },
			"cancel": function() { on_cancel(indicator); },
			"remove": function()
			{
				stack.removeChild(progress_cancel);
				stack.removeChild(progress_outer);
				stack.removeChild(label);
				if (stack.children.length === 0) stack.parentElement.removeChild(stack);
			}
		};

		if (on_cancel) progress_cancel.addEventListener("click", function() { indicator.cancel(); });

		return indicator;
	}

	function show_input_modal(modal_title, resolve_name, reject_name, hide_input)
	{
		const modal = document.createElement("div");
		modal.classList.add("modal");
		
		const modal_box = document.createElement("div");
		modal_box.classList.add("modal-box");

		const title_text = document.createElement("p");
		title_text.classList.add("modal-title");
		title_text.innerText = modal_title;

		const modal_input = document.createElement("input");
		modal_input.classList.add("modal-input");

		const resolve_button = document.createElement("button");
		resolve_button.classList.add("resolve-button");
		resolve_button.innerText = resolve_name;

		const reject_button = document.createElement("button");
		reject_button.classList.add("reject-button");
		reject_button.innerText = reject_name;

		modal_box.appendChild(title_text);
		if (!hide_input) modal_box.appendChild(modal_input);
		modal_box.appendChild(resolve_button);
		modal_box.appendChild(reject_button);

		modal.appendChild(modal_box);

		document.body.appendChild(modal);

		const result = new Promise(function(resolve, reject)
		{
			resolve_button.addEventListener("click", function()
			{
				modal.parentElement.removeChild(modal);
				resolve(modal_input.value);
			});
			reject_button.addEventListener("click", function()
			{
				modal.parentElement.removeChild(modal);
				reject()
			});
		});

		return result;
	}

	function add_entry_tile(entry)
	{
		if (entry === undefined) return;

		const link = document.createElement("a");
		if (entry.directory) link.href = `/drive/index.html?directory=${encodeURIComponent(entry.id)}`;
		else
		{
			link.href = "#";
			link.addEventListener("click", function() { download_file(entry.owner, entry.id); });
		}
		link.textContent = entry.name;

		const element = document.createElement("button");
		function replace_element_icon(new_icon)
		{
			const old_icons = element.getElementsByClassName("file-entry-icon");
			for (let i = 0; i < old_icons.length; i++) old_icons[i].parentElement.removeChild(old_icons[i]);
			new_icon.classList.add("file-entry-icon");
			element.insertBefore(new_icon, link);
		}
		function update_entry_icon()
		{
			get_element(entry.directory ? "/drive/folder.svg" : entry.public ? "/drive/public.svg" : "/drive/document.svg").then(replace_element_icon);
		}
		element.addEventListener("click", function()
		{
			link.click();
		});
		element.addEventListener("contextmenu", async function(e)
		{
			e.preventDefault();
			const menu = {
				"Open": function()
				{
					link.click();
				},
				"Rename": function()
				{
					show_input_modal("Rename", "Rename", "Cancel").then(function(new_name)
					{
						fetch(`/drive/rename?id=${encodeURIComponent(entry.id)}&name=${new_name}`, {
							"method": "POST",
							"headers": { "Authorization": session.get_token() }
						}).then(function(response)
						{
							if (response.ok) link.innerText = new_name;
						});
					});
				},
				"Delete": function()
				{
					show_input_modal("Delete", "Yes", "No", true).then(function()
					{
						fetch(`/drive/delete?id=${encodeURIComponent(entry.id)}`, {
							"method": "POST",
							"headers": { "Authorization": session.get_token() }
						}).then(function(response)
						{
							if (response.ok) element.parentElement.removeChild(element);
						});
					});
				}
			};

			function set_publish_status(status)
			{
				fetch(`/drive/publish?id=${encodeURIComponent(entry.id)}&public=${status ? "true" : "false"}`, {
					"method": "POST",
					"headers": { "Authorization": session.get_token() }
				}).then(function(response)
				{
					if (response.ok)
					{
						entry.public = status;
						update_entry_icon();
					}
				});
			}

			if (entry.public && !entry.directory)
			{
				menu["Copy Link"] = function() { navigator.clipboard.writeText(get_download_url(entry.owner, entry.id)); };
				menu["Make Private"] = function() { set_publish_status(false); };
			}
			else menu["Make Public"] = function() { set_publish_status(true); };

			await create_context_menu({ "x": e.clientX, "y": e.clientY }, menu);
		});
		element.classList.add("file-entry");
		element.appendChild(link);
		if (entry.directory) element.classList.add("directory");
		if (entry.public) element.classList.add("public");
		update_entry_icon();
		file_list.appendChild(element);
	}

	async function open_directory(id)
	{
		if (id !== undefined && id !== null)
		{
			fetch(`/drive/path?id=${encodeURIComponent(id)}`, {
				"method": "POST",
				"headers": { "Authorization": session.get_token() }
			}).then(async function(response)
			{
				if (response.ok)
				{
					const path = await response.json();
					if (path !== null) document.getElementById("header-title").innerText = `Drive - ${path}`;
					else window.location = "/drive/index.html";
				}
			});
		}

		const result = await get_directory_children(id);

		if (result.success)
		{
			while (file_list.lastChild) file_list.removeChild(file_list.lastChild);

			const add_button = document.createElement("button");
			add_button.classList.add("file-entry");
			add_button.appendChild(await get_element("/drive/add.svg"));
			add_button.addEventListener("click", function()
			{
				show_input_modal("Create Folder", "Create", "Cancel").then(function(new_name)
				{
					fetch(`/drive/directory/create?name=${encodeURIComponent(new_name)}` + (id ? `&parent=${encodeURIComponent(id)}` : ""), {
						"method": "POST",
						"headers": { "Authorization": session.get_token() }
					}).then(function (response)
					{
						if (response.ok) window.location.reload();
					});
				});
			});
			file_list.appendChild(add_button);

			result.children.forEach(function(child) { add_entry_tile(child); });
		}
	}

	async function get_directory_children(id)
	{
		function get_query()
		{
			if (id === undefined || id === null) return "/drive/directory/children";
			else return `/drive/directory/children?parent=${encodeURIComponent(id)}`;
		}

		const response = await fetch(get_query(), {
			"headers": {
				"Authorization": session.get_token()
			}
		});

		if (response.ok) return await response.json();
		else return { "success": false, "reason": response.status };
	}

	open_directory(current_directory);
});
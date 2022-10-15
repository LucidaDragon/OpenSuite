function go_to_redirect()
{
	window.location = new URLSearchParams(window.location.search).get("redirect") || "/dashboard/index.html";
}

if (window.sessionStorage.getItem("token")) go_to_redirect();

window.addEventListener("load", function()
{
	let is_register = true;
	const register_fold = document.getElementById("register-fold");
	const register_link = document.getElementById("register-link");
	const register_button = document.getElementById("register-button");
	const username_input = document.getElementById("username");
	const password_input = document.getElementById("password");
	const error_text = document.getElementById("error-text");

	function toggle_register()
	{
		is_register = !is_register;
		register_fold.style.visibility = is_register ? "visible" : "collapse";
		register_link.textContent = is_register ? "Sign In" : "Register";
		register_button.textContent = is_register ? "Register" : "Sign In";
		error_text.style.visibility = "collapse";
	}

	function show_error(message)
	{
		error_text.textContent = message;
		error_text.style.visibility = "visible";
	}

	async function process_inputs()
	{
		const username = username_input.value;
		const password = password_input.value;

		const response = await fetch((is_register ? "/auth/register" : "/auth/login") + `?username=${encodeURIComponent(username)}`, {
			"method": "POST",
			"body": password
		});

		if (response.ok)
		{
			const result = await response.json();

			if (result.success)
			{
				window.sessionStorage.setItem("token", result.token);
				go_to_redirect();
			}
			else if (is_register)
			{
				show_error("An account with that username already exists.");
			}
			else
			{
				show_error("Invalid credentials.");
			}
		}
		else
		{
			switch (response.status)
			{
				case 400:
					show_error("Username and password required.");
					break;
				case 401:
					show_error("Invalid credentials.");
					break;
				default:
					show_error(`Request returned error ${response.status}.`);
					break;
			}
		}
	}

	toggle_register();

	window.toggle_register = toggle_register;
	window.process_inputs = process_inputs;
});
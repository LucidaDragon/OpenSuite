addEventListener("DOMContentLoaded", () =>
{
	const days_of_week = ["S", "M", "T", "W", "T", "F", "S"];
	const year_input = document.getElementById("calendar-year");
	const month_input = document.getElementById("calendar-month");
	const calendar_grid = document.getElementById("calendar-grid");

	function on_selected_date_changed()
	{
		const current_date = new Date();
		const current_year = current_date.getFullYear();
		const current_month = current_date.getMonth();
		const year = isNaN(parseInt(year_input.value)) ? current_year : parseInt(year_input.value);
		const month = month_input.options.selectedIndex >= 1 || month_input.options.selectedIndex <= 12 ? month_input.options.selectedIndex : current_month;
		go_to_date(new Date(year, month, current_date.getDate()), current_year === year && current_month === month);
	}

	year_input.addEventListener("input", on_selected_date_changed);
	month_input.addEventListener("input", on_selected_date_changed);

	function days_in_month(date)
	{
		switch (date.getMonth())
		{
			case 0: return 31;
			case 1:
				const year = date.getFullYear();
				if ((year % 4) === 0)
				{
					if (year % 100)
					{
						if (year % 400) return 29;
						else return 28;
					}
					else return 29;
				}
				else return 28;
			case 2: return 31;
			case 3: return 30;
			case 4: return 31;
			case 5: return 30;
			case 6: return 31;
			case 7: return 31;
			case 8: return 30;
			case 9: return 31;
			case 10: return 30;
			case 11: return 31;
		}
	}

	function create_day_cell(date, selected)
	{
		function get_day_column(date)
		{
			return date.getDay() + 1;
		}

		function get_day_row(date)
		{
			if (date.getDate() === 1) return 2;
			const previous_day = new Date(date.getFullYear(), date.getMonth(), date.getDate() - 1);
			if (date.getDay() === 0) return get_day_row(previous_day) + 1;
			else return get_day_row(previous_day);
		}

		const cell = document.createElement("div");
		cell.id = `cell-${date.getDate()}`;
		cell.classList.add("calendar-cell");
		if (selected) cell.classList.add("today-cell");
		cell.style.gridRow = get_day_row(date);
		cell.style.gridColumn = get_day_column(date);

		const cell_day = document.createElement("div");
		cell_day.classList.add("calendar-cell-day");
		cell.appendChild(cell_day);

		const cell_day_number = document.createElement("div");
		cell_day_number.classList.add("calendar-cell-day-number");
		cell_day_number.innerText = date.getDate();
		cell_day.appendChild(cell_day_number);

		return cell;
	}

	function go_to_date(date, select)
	{
		if (select === undefined) select = false;

		year_input.value = date.getFullYear();
		month_input.options.selectedIndex = date.getMonth();
		calendar_grid.innerText = "";

		for (let i = 0; i < days_of_week.length; i++)
		{
			const weekday = document.createElement("span");
			weekday.classList.add("weekday-header");
			weekday.style.gridRow = 1;
			weekday.style.gridColumn = i + 1;
			weekday.innerText = days_of_week[i];
			calendar_grid.appendChild(weekday);
		}

		let last_row = 0;
		for (let i = 1; i < days_in_month(date) + 1; i++)
		{
			const cell = create_day_cell(new Date(date.getFullYear(), date.getMonth(), i), select && (i === date.getDate()));
			last_row = parseInt(cell.style.gridRow);
			calendar_grid.appendChild(cell);
		}

		let row_format = "max-content";
		for (let i = 0; i < last_row; i++) row_format += " auto";
		calendar_grid.style.gridTemplateRows = row_format;
	}

	go_to_date(new Date(), true);
});
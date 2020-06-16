Web application for R3IT

## Thoughts on Technology Choices

- JavaScript: don't use it, don't mutate the DOM.
- Build the web app like you would 25 years ago:
	- The users should interact only via form submission.
	- Dynamic changes to the interface should only be done via the templating language.
- HTML + CSS side:
	- For the alpha, don't use any CSS. Able to show improvement later.
	- Laying out HTML elements... no! It should look like a professor's website.
- For the backend:
	- Flask + Jinja2.
- The database?
	- Option A: some combination of CSV and json
	- Option B: sqlite
- Authentication: don't do it yet!

## Data Model

- applications_table
	- add_app()
	- approve_app()
	- run_interconn_analysis()
- engineering_constants
	- update()

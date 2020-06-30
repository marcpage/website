<html>
	<head>
		<title>${title}</title>
	</head>
	<body>
		<h1>${title}</h1>
		% if logged_in:
			Welcome!
		% else:
			<form action="/login" method="POST">
				<input name="email" placeholder="name@email.com"/>
				<input name="password" type="password" placeholder="password"/>
				<input type="submit" value="login">
			</form>
		% endif
	</body>
</body>

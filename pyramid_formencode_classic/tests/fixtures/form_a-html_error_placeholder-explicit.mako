<html><head></head><body><div>
<form action="/" method="POST">
    <% form = request.pyramid_formencode_classic.get_form() %>
    ${form.html_error_placeholder('Error_Main')|n}
    <input type="text" name="email" value="" />
    <input type="text" name="username" value="" />
</form>
</div></body></html>

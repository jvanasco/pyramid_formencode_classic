<form action="/" method="POST">
    <% form = request.pyramid_formencode_classic.get_form() %>
    ${form.html_error_main_fillable()|n}
    <input type="text" name="email" value="" />
</form>

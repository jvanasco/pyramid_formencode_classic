<form action="/" method="POST">
    <% form = request.pyramid_formencode_classic.get_form() %>
    ${form.html_error_main('Error_Main')|n}
    <input type="text" name="email" value="" />
</form>

document.addEventListener("DOMContentLoaded", function() {
    // Sucht den Header-Titel im MkDocs Material Layout
    var titleContainer = document.querySelector(".md-header__title");
    if (titleContainer && !titleContainer.querySelector("a")) {
        // Holt den aktuellen Text heraus
        var text = titleContainer.innerText.trim();
        // Ersetzt ihn durch einen Link zur Startseite (relativer Pfad "./")
        titleContainer.innerHTML = '<a href="./" style="color: inherit; text-decoration: none; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">' + text + '</a>';
    }
});

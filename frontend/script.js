document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("uploadForm");
    const linkList = document.getElementById("linkList");
    const message = document.getElementById("message");
    const addLinkButton = document.getElementById("addLink");

    let links = [];

    addLinkButton.addEventListener("click", () => {
        const newInput = document.createElement("input");
        newInput.type = "text";
        newInput.placeholder = "Enter Instagram Video Link";
        linkList.appendChild(newInput);
    });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        
        links = Array.from(linkList.querySelectorAll("input")).map(input => input.value).filter(Boolean);

        if (links.length === 0) {
            message.textContent = "Please enter at least one link.";
            return;
        }

        message.textContent = "Processing...";

        try {
            const response = await fetch("https://your-backend-url.com/process_videos/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ instagram_links: links }),
            });

            const data = await response.json();
            message.textContent = data.message;
        } catch (error) {
            message.textContent = "Error processing videos.";
        }
    });
});

window.onload = () => {
    document.getElementById("sendTextBtn").onclick = () => {

        // let selectElement = document.getElementById("languageSelect");

        fetch('http://127.0.0.1:5000/process_text', {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                "text": document.getElementById("inputText").value,
                "rate": document.getElementById("inputRate").checked,
                "language": document.getElementById("languageSelect").value
            })
        })
        .then(response => response.json())
        .then(response => {
            console.log(JSON.stringify(response));
            console.log(response[0]);
            localStorage.setItem("mapData", JSON.stringify(response[0]))
            window.location.href = "file:///Users/apple/Documents/dissertation/dissertation/game%20copy.html"
        })
        .catch(err => {
            console.log(err)
        })

    }
}
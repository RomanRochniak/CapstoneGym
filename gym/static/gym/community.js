document.addEventListener('DOMContentLoaded', function() {
});

function likeHandler(postId, initialLikedState) { 
    let liked = initialLikedState; 

    const url = liked ? `/gym/like_remove/${postId}/` : `/gym/like_add/${postId}/`;
    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(response => {
        if (!response.ok) {
            console.error("HTTP error:", response.status, response.statusText);
            return Promise.reject(new Error(response.statusText));
        }
        return response.json();
    })
    .then(data => {
        const likeButton = document.getElementById(`like_button_${postId}`);
        const likeIcon = document.getElementById(`like_icon_${postId}`);
        const likeCount = document.getElementById(`like_count_${postId}`);

        likeCount.textContent = data.like_count;

        // Toggle the liked state *after* the successful API call
        liked = !liked; // crucial line

        if (liked) { // crucial
            likeIcon.classList.remove('fa-regular');
            likeIcon.classList.add('fa-solid');
            likeButton.classList.add("liked");
        } else { // crucial
            likeIcon.classList.remove('fa-solid');
            likeIcon.classList.add('fa-regular');
            likeButton.classList.remove("liked");
        }

        // Update the button's onclick to reflect the new state
        likeButton.setAttribute('onclick', `likeHandler(${postId}, ${liked})`);
    })
    .catch(error => {
        console.error("Error updating like:", error);
    });
}

function handleSubmit(postId) {
    const content = document.getElementById(`textarea_${postId}`).value;
    fetch(`/gym/edit/${postId}`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            document.getElementById(`content_${postId}`).textContent = content;
            $(`#modal_edit_post_${postId}`).modal('hide');
        } else if (data.error) {
            console.error("Error:", data.error);
            alert(data.error);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

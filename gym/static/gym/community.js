document.addEventListener('DOMContentLoaded', function () {});

/**
 * Build URL safely regardless of whether routes are under /gym/ or not.
 * COMMUNITY_ENDPOINTS is injected from template:
 * window.COMMUNITY_ENDPOINTS = { likeAdd: ".../like_add/", likeRemove: ".../like_remove/" }
 */
function getEndpointUrl(action, postId) {
  const endpoints = window.COMMUNITY_ENDPOINTS || null;

  // Fallback if endpoints aren't injected (kept for safety)
  const fallbackBase =
    action === "remove" ? "/like_remove/" : "/like_add/";

  const base =
    endpoints && (action === "remove" ? endpoints.likeRemove : endpoints.likeAdd)
      ? (action === "remove" ? endpoints.likeRemove : endpoints.likeAdd)
      : fallbackBase;

  // Ensure base ends with "/" then append postId + "/"
  const normalized = base.endsWith("/") ? base : base + "/";
  return `${normalized}${postId}/`;
}

function likeHandler(postId, initialLikedState) {
  let liked = initialLikedState;

  const url = getEndpointUrl(liked ? "remove" : "add", postId);

  fetch(url, {
    method: "POST",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
  })
    .then((response) => {
      if (!response.ok) {
        console.error("HTTP error:", response.status, response.statusText);
        return Promise.reject(new Error(response.statusText));
      }
      return response.json();
    })
    .then((data) => {
      const likeButton = document.getElementById(`like_button_${postId}`);
      const likeIcon = document.getElementById(`like_icon_${postId}`);
      const likeCount = document.getElementById(`like_count_${postId}`);

      if (!likeButton || !likeIcon || !likeCount) return;

      likeCount.textContent = data.like_count;

      // Toggle the liked state after successful API call
      liked = !liked;

      if (liked) {
        likeIcon.classList.remove("fa-regular");
        likeIcon.classList.add("fa-solid");
        likeButton.classList.add("liked");
      } else {
        likeIcon.classList.remove("fa-solid");
        likeIcon.classList.add("fa-regular");
        likeButton.classList.remove("liked");
      }

      // Update onclick with new state
      likeButton.setAttribute("onclick", `likeHandler(${postId}, ${liked})`);
    })
    .catch((error) => {
      console.error("Error updating like:", error);
    });
}

function handleSubmit(postId) {
  const contentEl = document.getElementById(`textarea_${postId}`);
  if (!contentEl) return;

  const content = contentEl.value;

  // IMPORTANT: your route currently is /edit/<id> (not /gym/edit/<id>)
  fetch(`/edit/${postId}`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ content: content }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.message) {
        const out = document.getElementById(`content_${postId}`);
        if (out) out.textContent = content;
        $(`#modal_edit_post_${postId}`).modal("hide");
      } else if (data.error) {
        console.error("Error:", data.error);
        alert(data.error);
      }
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
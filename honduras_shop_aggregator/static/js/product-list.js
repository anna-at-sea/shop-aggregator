function bindLoadMoreButton() {
    const productList = document.getElementById("product-list");
    const loadMoreBtn = document.getElementById("load-more-btn");
    if (!loadMoreBtn) {
        return;
    }
    loadMoreBtn.onclick = function () {
        const nextPage = this.dataset.nextPage;
        const form = document.querySelector(
            ".filter-sidebar form"
        );
        const params = new URLSearchParams(
            new FormData(form)
        );
        params.set("page", nextPage);
        fetch(`?${params.toString()}`, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        })
        .then(response => response.json())
        .then(data => {
            productList.insertAdjacentHTML(
                "beforeend",
                data.products_html
            );
            attachLikeEvents();
            if (data.has_next) {
                this.dataset.nextPage = data.next_page;
            }
            else {
                this.remove();
            }
        });
    };
}

function attachLikeEvents() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    document.querySelectorAll('.like-btn').forEach(btn => {
        if (!btn.dataset.bound) {
            btn.dataset.bound = "true";
            btn.addEventListener('click', function () {
                const productId = this.dataset.productId;
                const url = toggleLikeUrl.replace('0', productId);
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                })
                .then(response => response.json())
                .then(data => {
                    this.textContent = data.status === 'liked' ? '❤️' : '🤍';
                })
                .catch(error => console.error('Error:', error));
            });
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    bindLoadMoreButton();
    attachLikeEvents();
});
'use strict';

$(document).ready(function () {
    let debounce;
    const DEBOUNCE_DELAY = 400;

    // Fetch and display suggested hashtags
    function fetchSuggestions(query) {
        $.ajax({
            type: "GET",
            url: '/posts/auto_correct/',
            data: { 'search_text': query },
            success: function (data) {
                $('#search-results').empty();
                for (let item of data) {
                    if (item.type === 'hashtag') {
                        let listItem = $('<li><i class="fas fa-hashtag"></i> ' + item.value + '</li>');
                        listItem.click(function () {
                            $('#search').val(item.value);
                            $('.search-bar').submit();
                        });
                        $('#search-results').append(listItem);
                    }
                }
            },
            error: function (error) {
                console.error("Error fetching search suggestions:", error.status, error.statusText);
            }
        });
    }

    $('#search').off('input').on('input', function (e) {
        clearTimeout(debounce);

        debounce = setTimeout(() => {
            fetchSuggestions($('#search').val());
        }, DEBOUNCE_DELAY);
    });

    // When the search input is focused, display suggested hashtags if the input is empty
    $('#search').on('focus', function () {
        if (!$(this).val()) {
            fetchSuggestions('');
        }
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('#search').length && !$(e.target).closest('#search-results').length) {
            $('#search-results').empty();
        }
    });
});
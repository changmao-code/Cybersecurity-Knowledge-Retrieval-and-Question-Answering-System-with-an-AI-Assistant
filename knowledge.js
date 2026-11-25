/* Render database content as text, including search terms and source titles. */
(() => {
  const form = document.querySelector('#search-form');
  const search = document.querySelector('#search');
  const filter = document.querySelector('#topic-filter');
  const cards = document.querySelector('#articles');
  const status = document.querySelector('#status');
  const submit = document.querySelector('#search-button');
  const reset = document.querySelector('#reset-search');
  const topicSlug = location.pathname.startsWith('/topics/') ? location.pathname.split('/')[2] : '';
  let topics = [];
  let pending;
  let sequence = 0;

  function node(tag, text, className) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  }

  async function json(url, options) {
    const response = await fetch(url, {cache: 'no-store', ...options});
    if (!response.ok) throw new Error('Request failed');
    return response.json();
  }

  function renderArticle(item) {
    const article = node('article', undefined, 'resource-card');
    const topic = topics.find(t => t.slug === item.topic);
    article.append(node('span', topic ? topic.title : item.topic, 'resource-topic'));
    article.append(node('h2', item.title), node('p', item.summary, 'resource-summary'));
    const details = node('details');
    const summary = node('summary', 'Read explanation');
    const body = node('div', undefined, 'explanation');
    details.append(summary, body);
    let loaded = false;
    let loading = false;
    details.addEventListener('toggle', async () => {
      if (!details.open || loaded || loading) return;
      loading = true;
      body.replaceChildren(node('p', 'Loading explanation...'));
      try {
        const data = await json('/api/articles/' + item.id);
        body.replaceChildren(node('p', data.content, 'content'));
        body.append(node('p', 'Introductory study summary. Consult the original source for full details.', 'study-note'));
        const source = node('p', undefined, 'source');
        const url = new URL(data.source_url);
        if (url.protocol === 'https:') {
          const link = node('a', data.source_title);
          link.href = url.href;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          source.append('Original source: ', link);
          body.append(source);
        }
        loaded = true;
      } catch (error) {
        body.replaceChildren(node('p', 'Unable to load this explanation. Close it and open it to try again.', 'error'));
      } finally {
        loading = false;
      }
    });
    article.append(details);
    return article;
  }

  async function loadArticles() {
    if (pending) pending.abort();
    pending = new AbortController();
    const current = ++sequence;
    submit.disabled = true;
    status.textContent = 'Loading resources...';
    cards.replaceChildren();
    const params = new URLSearchParams({q: search.value.trim()});
    if (filter && filter.value) params.set('topic', filter.value);
    const endpoint = topicSlug ? '/api/topics/' + encodeURIComponent(topicSlug) : '/api/articles';
    const browserParams = new URLSearchParams(params);
    if (!browserParams.get('q')) browserParams.delete('q');
    const query = browserParams.toString();
    history.replaceState(null, '', location.pathname + (query ? '?' + query : ''));
    try {
      const data = await json(endpoint + '?' + params, {signal: pending.signal});
      if (current !== sequence) return;
      status.textContent = data.articles.length
        ? `${data.articles.length} resource${data.articles.length === 1 ? '' : 's'} found.`
        : 'No results found. Try a different keyword or clear the search.';
      cards.replaceChildren(...data.articles.map(renderArticle));
    } catch (error) {
      if (error.name !== 'AbortError' && current === sequence) {
        status.textContent = 'Unable to load resources. Check the website connection and press Search to retry.';
      }
    } finally {
      if (current === sequence) submit.disabled = false;
    }
  }

  async function init() {
    try {
      const data = await json('/api/topics');
      topics = data.topics;
      const chosen = topics.find(t => t.slug === topicSlug);
      if (topicSlug && !chosen) throw new Error('Unknown topic');
      if (chosen) {
        document.querySelector('#page-title').textContent = chosen.title;
        document.querySelector('#breadcrumb-topic').textContent = chosen.title;
        document.querySelector('#page-intro').textContent = chosen.summary;
        document.title = chosen.title + ' | Cybersecurity Learning Hub';
        document.querySelector('#topic-badge').textContent = chosen.count + ' learning resources';
      } else {
        const grid = document.querySelector('#topic-cards');
        topics.forEach((topic, index) => {
          const link = node('a', undefined, 'topic-card topic-link');
          link.href = '/topics/' + topic.slug;
          link.append(node('span', String(index + 1).padStart(2, '0'), 'topic-number ' + topic.color));
          link.append(node('h3', topic.title), node('p', topic.summary));
          link.append(node('span', topic.count + ' resource' + (topic.count === 1 ? '' : 's'), 'count-label'));
          grid.append(link);
          const option = node('option', topic.title);
          option.value = topic.slug;
          filter.append(option);
        });
      }
      const params = new URLSearchParams(location.search);
      search.value = (params.get('q') || '').slice(0, 100);
      if (filter && topics.some(t => t.slug === params.get('topic'))) filter.value = params.get('topic');
      await loadArticles();
    } catch (error) {
      status.textContent = 'Unable to load the topic catalogue. Please refresh to try again.';
    }
  }

  form.addEventListener('submit', event => {event.preventDefault(); loadArticles();});
  if (filter) filter.addEventListener('change', loadArticles);
  reset.addEventListener('click', () => {
    search.value = '';
    if (filter) filter.value = '';
    loadArticles();
    search.focus();
  });
  init();
})();

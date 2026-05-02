const i18n = (() => {
  let data = {};
  let lang = 'en';

  async function load() {
    const res = await fetch('translations.json');
    data = await res.json();
  }

  function t(key) {
    return data[lang]?.[key] ?? key;
  }

  function getLang() { return lang; }

  function apply() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      el.innerHTML = t(el.dataset.i18nHtml);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    document.documentElement.lang = lang === 'vi' ? 'vi' : 'en';
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
  }

  function setLang(newLang) {
    lang = newLang;
    localStorage.setItem('lang', lang);
    document.dispatchEvent(new CustomEvent('langchange'));
  }

  return { load, t, getLang, setLang, apply };
})();

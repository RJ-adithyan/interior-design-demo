function nextShowcasePosition(positions, current, direction, maximum) {
  const stops = positions.map(position => Math.max(0, Math.min(maximum, position)));
  return direction > 0
    ? (stops.find(position => position > current + 1) ?? maximum)
    : ([...stops].reverse().find(position => position < current - 1) ?? 0);
}

if (typeof module !== 'undefined') module.exports = { nextShowcasePosition };

if (typeof document !== 'undefined') (() => {
  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const menu = document.querySelector('.mobile-menu');
  if (menu) {
    const trigger = menu.querySelector('summary');
    const background = [document.querySelector('main'), document.querySelector('.closing-cta'), document.querySelector('footer'), document.querySelector('.site-header .wordmark')].filter(Boolean);
    menu.addEventListener('toggle', () => {
      trigger.setAttribute('aria-expanded', String(menu.open));
      document.body.classList.toggle('menu-is-open', menu.open);
      background.forEach(element => { element.inert = menu.open; });
    });
    menu.addEventListener('keydown', event => {
      if (!menu.open) return;
      if (event.key === 'Escape') { event.preventDefault(); menu.open = false; trigger.focus(); }
      if (event.key === 'Tab') {
        const links = [...menu.querySelectorAll('summary, a[href]')];
        if (event.shiftKey && document.activeElement === links[0]) { event.preventDefault(); links.at(-1).focus(); }
        if (!event.shiftKey && document.activeElement === links.at(-1)) { event.preventDefault(); links[0].focus(); }
      }
    });
    menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => { menu.open = false; }));
    window.matchMedia('(min-width: 768px)').addEventListener('change', event => { if (event.matches) menu.open = false; });
  }

  const work = document.querySelector('[data-work]');
  if (work) {
    const filters = [...work.querySelectorAll('[data-work-category-filter]')];
    const categories = filters.map(link => link.dataset.workCategoryFilter);
    const render = () => {
      const value = new URLSearchParams(location.search).get('category') || 'all';
      const category = categories.find(item => item.toLowerCase() === value.toLowerCase()) || 'all';
      work.querySelectorAll('[data-work-project]').forEach(item => { item.hidden = category !== 'all' && item.dataset.category !== category; });
      filters.forEach(link => {
        if (link.dataset.workCategoryFilter === category) link.setAttribute('aria-current', 'true');
        else link.removeAttribute('aria-current');
      });
    };
    filters.forEach(link => link.addEventListener('click', event => {
      if (event.button || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      if (link.href !== location.href) history.pushState(null, '', link.href);
      render();
    }));
    window.addEventListener('popstate', render);
    render();
  }

  document.querySelectorAll('[data-showcase]').forEach(showcase => {
    const track = showcase.querySelector('[data-showcase-track]');
    const cards = [...showcase.querySelectorAll('[data-showcase-card]')];
    const previous = showcase.querySelector('[data-showcase-prev]');
    const next = showcase.querySelector('[data-showcase-next]');
    if (!track || !cards.length || !previous || !next) return;
    // Featured width stays independent of scroll position, so swipes never resize the track.
    cards[Math.min(1, cards.length - 1)].classList.add('is-featured');
    const syncControls = () => {
      previous.disabled = track.scrollLeft <= 1;
      next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 1;
    };
    const move = direction => {
      const viewport = track.getBoundingClientRect();
      const positions = cards.map(card => {
        const box = card.getBoundingClientRect();
        return track.scrollLeft + box.left + box.width / 2 - viewport.left - track.clientWidth / 2;
      });
      track.scrollTo({ left: nextShowcasePosition(positions, track.scrollLeft, direction, track.scrollWidth - track.clientWidth), behavior: motion.matches ? 'instant' : 'smooth' });
    };
    previous.addEventListener('click', () => move(-1));
    next.addEventListener('click', () => move(1));
    track.addEventListener('scroll', syncControls, { passive: true });
    window.addEventListener('resize', syncControls);
    syncControls();
  });

  if (!motion.matches && 'IntersectionObserver' in window && Element.prototype.animate) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        if (motion.matches) return;
        const image = entry.target.dataset.reveal === 'image';
        entry.target.animate([{ opacity: .12, transform: 'translateY(20px)' }, { opacity: 1, transform: 'translateY(0)' }], { duration: image ? 750 : 550, easing: 'cubic-bezier(.2,.7,.2,1)' });
        if (image) entry.target.querySelector('img')?.animate([{ transform: 'scale(1.04)' }, { transform: 'scale(1)' }], { duration: 850, easing: 'cubic-bezier(.2,.7,.2,1)' });
      });
    }, { threshold: .13 });
    document.querySelectorAll('[data-reveal]').forEach(element => observer.observe(element));
    motion.addEventListener('change', event => { if (event.matches) { observer.disconnect(); document.getAnimations().forEach(animation => animation.cancel()); } });
  }
})();

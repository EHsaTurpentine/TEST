const APP = document.getElementById('app');
let MANIFEST = null;

async function loadManifest() {
  if (MANIFEST) return MANIFEST;
  const res = await fetch('manifest.json', { cache: 'no-store' });
  MANIFEST = await res.json();
  return MANIFEST;
}

function escapeHtml(str) {
  return str.replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function formatDate(d) {
  if (!d) return '';
  const [y, m, day] = d.split('-');
  if (!m) return y;
  const months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  return `${months[parseInt(m, 10) - 1]} ${y}`;
}

// ---------- index view ----------

function renderIndex(manifest) {
  const projects = manifest.projects || [];

  if (projects.length === 0) {
    APP.innerHTML = `
      <div class="catalog">
        <p class="catalog__empty">Nothing archived yet. Drop a folder into /content and push.</p>
      </div>`;
    return;
  }

  const rows = projects.map((p) => `
    <a class="catalog__row" href="#/${encodeURIComponent(p.slug)}">
      <span class="catalog__date">${escapeHtml(formatDate(p.date))}</span>
      <span>
        <span class="catalog__title">${escapeHtml(p.title)}</span>
        ${p.description ? `<span class="catalog__desc">${escapeHtml(p.description)}</span>` : ''}
      </span>
      <span class="catalog__count">${p.files.length} file${p.files.length === 1 ? '' : 's'}</span>
    </a>
  `).join('');

  APP.innerHTML = `<div class="catalog">${rows}</div>`;
}

// ---------- project detail view ----------

async function renderFileBlock(file) {
  const wrap = document.createElement('div');
  wrap.className = `file-block file-block--${file.type}`;

  const label = document.createElement('div');
  label.className = 'file-block__label';
  label.innerHTML = `<span>${escapeHtml(file.name)}</span><a href="${encodeURIComponent(file.path)}" download>download</a>`;
  wrap.appendChild(label);

  const body = document.createElement('div');

  switch (file.type) {
    case 'markdown': {
      try {
        const res = await fetch(file.path);
        const text = await res.text();
        body.innerHTML = marked.parse(text);
      } catch {
        body.innerHTML = `<p class="converted-note">Couldn't load this file.</p>`;
      }
      break;
    }
    case 'pdf': {
      body.innerHTML = `<iframe src="${encodeURIComponent(file.path)}" title="${escapeHtml(file.name)}"></iframe>`;
      break;
    }
    case 'image': {
      body.innerHTML = `<img src="${encodeURIComponent(file.path)}" alt="${escapeHtml(file.name)}" loading="lazy">`;
      break;
    }
    case 'audio': {
      body.innerHTML = `<audio controls src="${encodeURIComponent(file.path)}"></audio>`;
      break;
    }
    case 'video': {
      body.innerHTML = `<video controls src="${encodeURIComponent(file.path)}"></video>`;
      break;
    }
    default: {
      body.innerHTML = `<a href="${encodeURIComponent(file.path)}" download>Download ${escapeHtml(file.name)}</a>`;
    }
  }

  wrap.appendChild(body);

  if (file.originalName) {
    const note = document.createElement('p');
    note.className = 'converted-note';
    note.innerHTML = `Converted from ${escapeHtml(file.originalName)} · <a href="${encodeURIComponent(file.original)}" download>download original</a>`;
    wrap.appendChild(note);
  }

  return wrap;
}

async function renderProject(manifest, slug) {
  const project = (manifest.projects || []).find((p) => p.slug === slug);

  if (!project) {
    APP.innerHTML = `
      <div class="project">
        <a class="project__back" href="#/">&larr; back</a>
        <p class="catalog__empty">Project not found.</p>
      </div>`;
    return;
  }

  APP.innerHTML = `
    <div class="project">
      <a class="project__back" href="#/">&larr; index</a>
      <h1 class="project__title">${escapeHtml(project.title)}</h1>
      ${project.date ? `<div class="project__date">${escapeHtml(formatDate(project.date))}</div>` : ''}
      ${project.description ? `<p class="project__desc">${escapeHtml(project.description)}</p>` : ''}
      <div class="project__files" id="project-files"></div>
    </div>`;

  const container = document.getElementById('project-files');
  if (project.files.length === 0) {
    container.innerHTML = `<p class="catalog__empty">No files in this project yet.</p>`;
    return;
  }

  for (const file of project.files) {
    const block = await renderFileBlock(file);
    container.appendChild(block);
  }
}

// ---------- router ----------

async function route() {
  const manifest = await loadManifest();
  const hash = location.hash.replace(/^#\/?/, '');
  if (!hash) {
    renderIndex(manifest);
  } else {
    renderProject(manifest, decodeURIComponent(hash));
  }
  window.scrollTo(0, 0);
}

window.addEventListener('hashchange', route);
window.addEventListener('DOMContentLoaded', route);

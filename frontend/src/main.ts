import './atlas/tokens.css';
import './atlas/components.css';
import './islands.css';
import './site.css';
import './studio.css';
import { boot } from './boot';

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => boot(document), { once: true });
} else {
  boot(document);
}

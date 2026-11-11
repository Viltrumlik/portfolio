import { afterEach, describe, expect, it } from 'vitest';
import { initTemplatePreview, renderTemplate } from './template-preview';

afterEach(() => {
  document.body.innerHTML = '';
});

describe('renderTemplate', () => {
  const sample = { repo: 'volunteers_bot', tag: 'v1.2', release: { name: 'Spring', stars: 12, draft: false } };

  it('replaces {{key}} and tolerates inner spaces', () => {
    expect(renderTemplate('Shipped {{repo}} {{ tag }}', sample)).toBe('Shipped volunteers_bot v1.2');
  });

  it('follows dotted paths', () => {
    expect(renderTemplate('{{release.name}} ({{release.stars}}, draft={{release.draft}})', sample)).toBe(
      'Spring (12, draft=false)',
    );
  });

  it('renders missing keys, objects and inherited properties as empty strings', () => {
    expect(renderTemplate('[{{nope}}][{{release.nope.deeper}}][{{release}}]', sample)).toBe('[][][]');
    expect(renderTemplate('[{{constructor}}][{{__proto__}}][{{repo.length}}]', sample)).toBe('[][][]');
  });

  it('leaves text that is not a placeholder alone', () => {
    expect(renderTemplate('{ {repo} } {{}} {{ bad key }}', sample)).toBe('{ {repo} } {{}} {{ bad key }}');
  });
});

describe('initTemplatePreview', () => {
  function mount(sample: string) {
    document.body.innerHTML = `
      <div data-island="template-preview" data-sample='${sample}'>
        <textarea data-template-input>New release {{repo}} {{tag}}</textarea>
        <p data-template-output></p>
      </div>`;
    const root = document.querySelector<HTMLElement>('[data-island="template-preview"]')!;
    initTemplatePreview(root);
    return {
      input: root.querySelector<HTMLTextAreaElement>('[data-template-input]')!,
      output: root.querySelector<HTMLElement>('[data-template-output]')!,
    };
  }

  it('renders on init and on every input', () => {
    const { input, output } = mount('{"repo":"volunteers_bot","tag":"v1.2"}');
    expect(output.textContent).toBe('New release volunteers_bot v1.2');
    input.value = '{{tag}} is out';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    expect(output.textContent).toBe('v1.2 is out');
  });

  it('never injects HTML', () => {
    const { input, output } = mount('{"repo":"<b>bold</b>"}');
    input.value = '<i>{{repo}}</i>';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    expect(output.textContent).toBe('<i><b>bold</b></i>');
    expect(output.children.length).toBe(0);
  });

  it('treats an invalid sample as empty', () => {
    const { output } = mount('{not json');
    expect(output.textContent).toBe('New release  ');
  });
});

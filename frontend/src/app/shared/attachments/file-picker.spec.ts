import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FilePicker } from './file-picker';

function file(name: string, bytes = 10): File {
  return new File([new Uint8Array(bytes)], name);
}

describe('FilePicker', () => {
  let fixture: ComponentFixture<FilePicker>;
  let picker: FilePicker;

  beforeEach(() => {
    // No config loaded: the picker uses the default limits (10 MB per file, 5 files).
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    fixture = TestBed.createComponent(FilePicker);
    picker = fixture.componentInstance;
    fixture.detectChanges();
  });

  function errors(): string {
    fixture.detectChanges();
    return (fixture.nativeElement.querySelector('.errors')?.textContent ?? '') as string;
  }

  it('accepts allowed files and lists them', () => {
    picker.add([file('screenshot.png'), file('error.log')]);
    fixture.detectChanges();
    expect(picker.files().map((f) => f.name)).toEqual(['screenshot.png', 'error.log']);
    expect(fixture.nativeElement.querySelectorAll('.chosen li').length).toBe(2);
  });

  it('rejects file types the backend does not allow', () => {
    picker.add([file('setup.exe'), file('drawing.svg'), file('notes.txt')]);
    expect(picker.files().map((f) => f.name)).toEqual(['notes.txt']);
    expect(errors()).toContain('setup.exe: this file type is not allowed.');
    expect(errors()).toContain('drawing.svg: this file type is not allowed.');
  });

  it('rejects files over the size limit', () => {
    picker.add([file('huge.log', 10 * 1024 * 1024 + 1)]);
    expect(picker.files().length).toBe(0);
    expect(errors()).toContain('huge.log is 10.0 MB; the limit is 10 MB per file.');
  });

  it('stops at the maximum number of files', () => {
    picker.add([1, 2, 3, 4, 5, 6].map((n) => file(`log-${n}.txt`)));
    expect(picker.files().length).toBe(5);
    expect(errors()).toContain('You can attach up to 5 files at a time.');
  });

  it('removes a chosen file', () => {
    const first = file('a.log');
    picker.add([first, file('b.log')]);
    picker.remove(first);
    expect(picker.files().map((f) => f.name)).toEqual(['b.log']);
  });
});

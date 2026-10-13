/* SWARM: accessible navigation and a dimensional bee built from the swarm. */
(() => {
'use strict';
document.documentElement.classList.add('rd-enhanced');
const toggle=document.querySelector('.rd-menu-toggle');
const menu=toggle&&document.getElementById(toggle.getAttribute('aria-controls'));
if(toggle&&menu){
 const setMenu=open=>{toggle.setAttribute('aria-expanded',String(open));toggle.textContent=open?'Close':'Menu';menu.classList.toggle('is-open',open);if(open)menu.querySelector('a')?.focus();};
 toggle.addEventListener('click',()=>setMenu(toggle.getAttribute('aria-expanded')!=='true'));
 menu.addEventListener('click',e=>{if(e.target.closest('a'))setMenu(false);});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&toggle.getAttribute('aria-expanded')==='true'){setMenu(false);toggle.focus();}});
 document.addEventListener('click',e=>{if(!e.target.closest('.rd-header'))setMenu(false);});
 matchMedia('(min-width:981px)').addEventListener('change',e=>{if(e.matches)setMenu(false);});
}
})();

const slider=document.querySelector('#pzero');
function update(){const n=Number(slider.value), p=n/100;document.querySelector('#readout').textContent=`P(0) = ${p.toFixed(2)} · P(1) = ${(1-p).toFixed(2)} · average Z = ${(2*p-1).toFixed(2)}`;document.querySelector('.zero').style.width=n+'%';document.querySelector('.one').style.width=(100-n)+'%'}
if(slider){slider.addEventListener('input',update);update()}
for(const f of document.querySelectorAll('form[data-answer]'))f.addEventListener('submit',e=>{e.preventDefault();const v=f.querySelector('input').value;f.querySelector('output').textContent=v!==''&&Math.abs(Number(v)-Number(f.dataset.answer))<1e-8?'Correct. '+f.dataset.explanation:'Try again. '+f.dataset.hint});

#!/usr/bin/env python3
"""Intrinsic Shor task-fibre advantage freeze-candidate v0.9.3.

Runs an exact state-vector phase-estimation model for N=15, a=2 (order r=4),
including the inverse QFT measurement distribution.  It optimises the
probability of measuring a continued-fraction bin that recovers the exact
order, while keeping the declared ideal modular-multiplication response on an
exact four-dimensional fibre.  Synthetic coherent/dephasing noise, not QPU.

Only NumPy is required. Notebook-injected arguments such as -f are ignored.
"""
from __future__ import annotations
import argparse, json, math, sys
from dataclasses import dataclass
import numpy as np

VERSION="0.9.3"
N,A_BASE,ORDER=15,2,4
CONTROL_QUBITS=4
M=2**CONTROL_QUBITS
N_PARAM=9

# Five independent declared-response coordinates and one dependent audit row.
A=np.array([
 [1,0,0,-1,0,0,0,0,0], [0,1,0,0,0,1,1,0,0],
 [0,0,1,0,0,0,0,0,1], [0,0,0,0,1,0,0,0,0],
 [0,0,0,0,0,0,0,1,0], [1,1,1,-1,0,1,1,1,1]],float)
J_DAG=np.linalg.pinv(A,rcond=1e-12)
P_T=np.eye(N_PARAM)-J_DAG@A
P_N=np.eye(N_PARAM)-P_T

# Shared hardware sensitivity makes training/held-out generalisation testable;
# seed-specific perturbations and a shifted held-out law prevent identity reuse.
_rg=np.random.default_rng(1502)
COMMON_C=_rg.normal(size=(CONTROL_QUBITS,N_PARAM))
COMMON_C/=np.linalg.norm(COMMON_C,axis=1,keepdims=True)

# Explicit 15-dimensional multiplier, embedded in 16 dimensions.
U_MULT=np.zeros((16,16),complex)
for x in range(16):
    y=(A_BASE*x)%N if x<N else 15
    U_MULT[y,x]=1


@dataclass
class Ledger:
    noisy_task_calls:int=0
    response_calls:int=0
    proposals:int=0
    steps:int=0
    @property
    def total(self): return self.noisy_task_calls+self.response_calls


def response(theta,ledger=None):
    if ledger is not None: ledger.response_calls+=1
    return A@np.asarray(theta,float)


def ideal_multiplier(theta):
    # Five commuting implementation phases; they disappear exactly on Aθ=0.
    q=A[:5]@np.asarray(theta,float)
    signs=np.array([[1 if ((x>>j)&1)==0 else -1 for x in range(16)]
                    for j in range(4)],float)
    g=np.vstack([signs,signs[0]*signs[1]])
    return U_MULT@np.diag(np.exp(-.5j*(q@g)))


def noise_instance(seed,shifted=False):
    rng=np.random.default_rng(seed)
    d=rng.normal(size=(CONTROL_QUBITS,N_PARAM)); d/=np.linalg.norm(d,axis=1,keepdims=True)
    C=COMMON_C+(0.10 if not shifted else 0.17)*d
    C/=np.linalg.norm(C,axis=1,keepdims=True)
    common=np.array([.105,-.082,.064,-.047])
    eps=common+rng.normal(0,.010 if not shifted else .016,CONTROL_QUBITS)
    dephase=float(np.clip((.025 if not shifted else .040)+rng.normal(0,.004),0,.15))
    return C,eps,dephase


def iqft_probabilities(theta,seed,shifted=False):
    """Mixture over the four exact eigenphases s/r, followed by inverse QFT."""
    C,base,dephase=noise_instance(seed,shifted)
    eps=base+0.72*(C@np.asarray(theta,float))
    x=np.arange(M)
    bits=np.array([[(xx>>k)&1 for k in range(CONTROL_QUBITS)] for xx in x])
    implementation_phase=bits@eps
    p=np.zeros(M)
    for s in range(ORDER):
        state=np.exp(2j*np.pi*s*x/ORDER+1j*implementation_phase)/math.sqrt(M)
        amp=np.fft.fft(state)/math.sqrt(M)  # inverse-QFT probabilities up to convention
        p+=np.abs(amp)**2/ORDER
    p=(1-dephase)*p+dephase*np.ones(M)/M
    return p/p.sum()


SUCCESS_BINS=[M//4,3*M//4]  # y/M=1/4 or 3/4 -> continued fraction denominator 4


def ideal_order_success():
    x=np.arange(M);p=np.zeros(M)
    for s in range(ORDER):
        state=np.exp(2j*np.pi*s*x/ORDER)/math.sqrt(M)
        p+=np.abs(np.fft.fft(state)/math.sqrt(M))**2/ORDER
    return float(np.sum(p[SUCCESS_BINS]))


def seed_success(theta,seed,shifted=False):
    p=iqft_probabilities(theta,seed,shifted)
    return float(np.sum(p[SUCCESS_BINS]))


def mean_success(theta,seeds,shifted=False,ledger=None):
    if ledger is not None: ledger.noisy_task_calls+=len(seeds)
    return float(np.mean([seed_success(theta,s,shifted) for s in seeds]))


def loss(theta,seeds,ledger):
    # Response penalty makes normal drift operationally visible; task success
    # remains the reported endpoint and the sole held-out ranking quantity.
    return 1-mean_success(theta,seeds,ledger=ledger)+.30*np.mean((A@theta)**2)


def gradient(theta,seeds,ledger,eps=2e-5):
    g=np.zeros(N_PARAM)
    for j in range(N_PARAM):
        d=np.zeros(N_PARAM);d[j]=eps
        g[j]=(loss(theta+d,seeds,ledger)-loss(theta-d,seeds,ledger))/(2*eps)
    return g


def drifts(meta,steps,scale):
    rng=np.random.default_rng(meta^0x901D)
    out=[]
    for _ in range(steps):
        v=P_N@rng.normal(size=N_PARAM)
        out.append(scale*v/max(np.linalg.norm(v),1e-15))
    return out


def run_flow(seeds,meta,steps,lr,beta,drift_scale,hybrid):
    theta=np.zeros(N_PARAM); led=Ledger(); max_res=0.
    for drift in drifts(meta,steps,drift_scale):
        theta+=drift
        g=gradient(theta,seeds,led)
        theta-=lr*(P_T@g)
        e=response(theta,led)
        if hybrid:
            theta-=beta*(J_DAG@e)
        e=response(theta,led)  # identical two-call accounting in both arms
        max_res=max(max_res,float(np.linalg.norm(e)));led.steps+=1
    return theta,led,max_res


def random_search(seeds,budget,meta,rmax=1.6):
    rng=np.random.default_rng(meta^0xB4515);led=Ledger();best=np.zeros(N_PARAM)
    bestv=mean_success(best,seeds,ledger=led)
    while led.total+len(seeds)<=budget:
        v=P_T@rng.normal(size=N_PARAM); nv=np.linalg.norm(v)
        if nv<1e-14:continue
        cand=rmax*rng.random()**.25*v/nv;led.proposals+=1
        val=mean_success(cand,seeds,ledger=led)
        if val>bestv:best,bestv=cand,val
    # Spend the response-call remainder without changing the selected point.
    while led.total<budget: response(best,led)
    return best,led


def tangent_basis():
    w,v=np.linalg.eigh((P_T+P_T.T)/2)
    return v[:,w>.5]


T_BASIS=tangent_basis()


def exact_flow(seeds,budget,lr=.28):
    """Feasible projected task-gradient flow; no injected normal drift."""
    theta=np.zeros(N_PARAM);led=Ledger()
    while led.total+2*N_PARAM*len(seeds)<=budget:
        g=gradient(theta,seeds,led)
        theta-=lr*(P_T@g);led.steps+=1
    while led.total<budget:response(theta,led)
    return theta,led


def spsa_search(seeds,budget,meta,lr=.18,c=.03):
    """Basis-coordinate SPSA: a stronger derivative-free exact-fibre baseline."""
    rng=np.random.default_rng(meta^0x5A5A);z=np.zeros(T_BASIS.shape[1]);led=Ledger();k=0
    while led.total+2*len(seeds)<=budget:
        d=rng.choice([-1.,1.],size=len(z))
        fp=1-mean_success(T_BASIS@(z+c*d),seeds,ledger=led)
        fm=1-mean_success(T_BASIS@(z-c*d),seeds,ledger=led)
        g=(fp-fm)/(2*c)*d
        z-=lr/(1+.02*k)*g;k+=1;led.proposals+=1
    theta=T_BASIS@z
    while led.total<budget:response(theta,led)
    return theta,led


def local_task_geometry(seeds,h=2e-3):
    """Central-difference task gradient and Hessian in orthonormal fibre coordinates."""
    d=T_BASIS.shape[1];z0=np.zeros(d)
    def f(z):return mean_success(T_BASIS@z,seeds)
    f0=f(z0);g=np.zeros(d);H=np.zeros((d,d))
    for i in range(d):
        ei=np.zeros(d);ei[i]=h
        g[i]=(f(ei)-f(-ei))/(2*h)
        H[i,i]=(f(ei)-2*f0+f(-ei))/h**2
        for j in range(i):
            ej=np.zeros(d);ej[j]=h
            H[i,j]=H[j,i]=(f(ei+ej)-f(ei-ej)-f(-ei+ej)+f(-ei-ej))/(4*h*h)
    return g,H


def charged_intrinsic_gradient(z,seeds,ledger,h=2e-5):
    d=len(z);g=np.zeros(d)
    for i in range(d):
        e=np.zeros(d);e[i]=h
        g[i]=(mean_success(T_BASIS@(z+e),seeds,ledger=ledger)-
              mean_success(T_BASIS@(z-e),seeds,ledger=ledger))/(2*h)
    return g


def charged_reference_hessian(seeds,ledger,h=2e-3):
    d=T_BASIS.shape[1];z=np.zeros(d);H=np.zeros((d,d))
    f0=mean_success(T_BASIS@z,seeds,ledger=ledger)
    fp=[];fm=[]
    for i in range(d):
        e=np.zeros(d);e[i]=h
        fp.append(mean_success(T_BASIS@e,seeds,ledger=ledger))
        fm.append(mean_success(-T_BASIS@e,seeds,ledger=ledger))
        H[i,i]=(fp[-1]-2*f0+fm[-1])/h**2
    for i in range(d):
      for j in range(i):
        ei=np.zeros(d);ej=np.zeros(d);ei[i]=h;ej[j]=h
        vals=[mean_success(T_BASIS@q,seeds,ledger=ledger)
              for q in (ei+ej,ei-ej,-ei+ej,-ei-ej)]
        H[i,j]=H[j,i]=(vals[0]-vals[1]-vals[2]+vals[3])/(4*h*h)
    return H


def intrinsic_flow(seeds,budget,preconditioned,meta,trust=.10):
    """Four-dimensional feasible ascent; every task/response call is charged."""
    z=np.zeros(T_BASIS.shape[1]);led=Ledger();H=None
    if preconditioned:
        H=charged_reference_hessian(seeds,led)
        w,Q=np.linalg.eigh(-(H+H.T)/2)
        floor=max(5e-4,.03*np.max(np.abs(w)))
        inv=Q@np.diag(1/np.maximum(np.abs(w),floor))@Q.T
    while led.total+(2*len(z)+3)*len(seeds)<=budget:
        g=charged_intrinsic_gradient(z,seeds,led)
        direction=inv@g if preconditioned else g
        nd=np.linalg.norm(direction)
        if nd<1e-14:break
        direction*=min(1.,trust/nd)
        base=mean_success(T_BASIS@z,seeds,ledger=led)
        bestz=z;best=base
        for alpha in (1.,.5):
            cand=z+alpha*direction
            val=mean_success(T_BASIS@cand,seeds,ledger=led)
            if val>best:bestz,best=cand,val;break
        z=bestz;led.steps+=1
    theta=T_BASIS@z
    while led.total<budget:response(theta,led)
    return theta,led,([] if H is None else np.linalg.eigvalsh(H).tolist())


def gate_proxy(theta,seeds,shifted=False):
    vals=[]
    for seed in seeds:
        C,b,d=noise_instance(seed,shifted);phase=b+.72*(C@theta)
        vals.append(d+np.mean(np.sin(phase)**2))
    return float(np.mean(vals))


def ranks(x):
    order=np.argsort(x,kind='mergesort');r=np.empty(len(x),float);r[order]=np.arange(len(x))
    return r


def corr(x,y):
    x=np.asarray(x,float);y=np.asarray(y,float)
    if np.std(x)<1e-15 or np.std(y)<1e-15:return 0.
    return float(np.corrcoef(x,y)[0,1])


def bootstrap_ci(x,seed,draws):
    x=np.asarray(x,float);rng=np.random.default_rng(seed)
    z=np.mean(rng.choice(x,(draws,len(x)),replace=True),axis=1)
    return [float(np.quantile(z,.025)),float(np.quantile(z,.975))]


def sign_p(x):
    pos=sum(v>0 for v in x);neg=sum(v<0 for v in x);n=pos+neg
    if not n:return 1.
    k=min(pos,neg)
    return float(min(1,2*sum(math.comb(n,i) for i in range(k+1))/2**n))


def parse():
    p=argparse.ArgumentParser()
    p.add_argument('--meta-seeds',type=int,default=12)
    p.add_argument('--steps',type=int,default=60)
    p.add_argument('--lr',type=float,default=.28)
    p.add_argument('--beta',type=float,default=1.)
    p.add_argument('--drift-scale',type=float,default=.002)
    p.add_argument('--bootstrap',type=int,default=10000)
    p.add_argument('--landscape-samples',type=int,default=256)
    p.add_argument('--json-out',default='shor_order_finding_v0_9_3_result.json')
    return p.parse_known_args()


def main():
    a,unknown=parse()
    if unknown:print(f'[notice] ignored notebook/kernel arguments: {unknown}')
    records=[]
    for m in range(a.meta_seeds):
        meta=20260817+1009*m;rng=np.random.default_rng(meta)
        train=[int(v) for v in rng.integers(1,2**31-1,5)]
        held=[int(v) for v in rng.integers(1,2**31-1,8)]
        tt,lt,rt=run_flow(train,meta,a.steps,a.lr,a.beta,a.drift_scale,False)
        th,lh,rh=run_flow(train,meta,a.steps,a.lr,a.beta,a.drift_scale,True)
        tr,lr=random_search(train,lh.total,meta)
        te,le=exact_flow(train,lh.total,a.lr)
        ts,ls=spsa_search(train,lh.total,meta)
        ti,li,_=intrinsic_flow(train,lh.total,False,meta)
        tp,lp,hpre=intrinsic_flow(train,lh.total,True,meta)
        b=mean_success(np.zeros(N_PARAM),held,True)
        st=mean_success(tt,held,True);sh=mean_success(th,held,True);sr=mean_success(tr,held,True)
        se=mean_success(te,held,True);ss=mean_success(ts,held,True)
        si=mean_success(ti,held,True);spc=mean_success(tp,held,True)
        row={'meta_seed':meta,'success_before':b,'success_tangent':st,
             'success_hybrid':sh,'success_basis_invariant_random':sr,
             'success_exact_fibre_flow':se,'success_exact_fibre_spsa':ss,
             'success_intrinsic_euclidean':si,'success_hessian_preconditioned':spc,
             'hybrid_minus_random':sh-sr,'hybrid_minus_tangent':sh-st,
             'exact_flow_minus_random':se-sr,'exact_flow_minus_spsa':se-ss,
             'preconditioned_minus_random':spc-sr,
             'preconditioned_minus_spsa':spc-ss,
             'preconditioned_minus_intrinsic_euclidean':spc-si,
             'intrinsic_minus_random':si-sr,
             'intrinsic_minus_spsa':si-ss,
             'intrinsic_minus_before':si-b,
             'tangent_budget':lt.total,'hybrid_budget':lh.total,'random_budget':lr.total,
             'exact_flow_budget':le.total,'spsa_budget':ls.total,
             'intrinsic_euclidean_budget':li.total,'preconditioned_budget':lp.total,
             'preconditioner_reference_hessian_eigenvalues':hpre,
             'max_response_residual_tangent':rt,'max_response_residual_hybrid':rh,
             'final_hybrid_response_residual':float(np.linalg.norm(response(th))),
             'hybrid_ideal_multiplier_change':float(np.linalg.norm(ideal_multiplier(th)-U_MULT)),
             'random_ideal_multiplier_change':float(np.linalg.norm(ideal_multiplier(tr)-U_MULT)),
             'random_normal_component':float(np.linalg.norm(P_N@tr))}
        records.append(row)
        print(f'[{m+1:02d}/{a.meta_seeds}] pre={spc:.8f} intrinsic={si:.8f} random={sr:.8f} spsa={ss:.8f} budget={lh.total}')
    hr=[r['hybrid_minus_random'] for r in records];ht=[r['hybrid_minus_tangent'] for r in records]
    cihr=bootstrap_ci(hr,20260816,a.bootstrap);ciht=bootstrap_ci(ht,20260817,a.bootstrap)
    gaps=[max(r['tangent_budget'],r['hybrid_budget'],r['random_budget'])-
          min(r['tangent_budget'],r['hybrid_budget'],r['random_budget']) for r in records]
    budget_keys=('tangent_budget','hybrid_budget','random_budget','exact_flow_budget','spsa_budget','intrinsic_euclidean_budget','preconditioned_budget')
    all_gaps=[max(r[k] for k in budget_keys)-min(r[k] for k in budget_keys) for r in records]
    # Frozen landscape diagnostic at the first meta-seed's training law.
    rr=np.random.default_rng(991);train0=np.random.default_rng(20260817).integers(1,2**31-1,5).tolist()
    tg,H=local_task_geometry(train0);he=np.linalg.eigvalsh(H)
    xs=[];gp=[];sp=[]
    for _ in range(a.landscape_samples):
        raw=rr.normal(size=4);z=1.2*rr.random()**.25*raw/max(np.linalg.norm(raw),1e-15)
        theta=T_BASIS@z;gp.append(gate_proxy(theta,train0));sp.append(mean_success(theta,train0));xs.append(theta)
    pear=corr(gp,sp);spear=corr(ranks(gp),ranks(sp))
    conflict=float(np.mean([(gp[i]<gate_proxy(np.zeros(N_PARAM),train0)) !=
                            (sp[i]>mean_success(np.zeros(N_PARAM),train0)) for i in range(len(gp))]))
    efr=[r['exact_flow_minus_random'] for r in records];efs=[r['exact_flow_minus_spsa'] for r in records]
    ciefr=bootstrap_ci(efr,20260818,a.bootstrap);ciefs=bootstrap_ci(efs,20260819,a.bootstrap)
    pr=[r['preconditioned_minus_random'] for r in records]
    ps=[r['preconditioned_minus_spsa'] for r in records]
    pi=[r['preconditioned_minus_intrinsic_euclidean'] for r in records]
    cipr=bootstrap_ci(pr,20260820,a.bootstrap);cips=bootstrap_ci(ps,20260821,a.bootstrap);cipi=bootstrap_ci(pi,20260822,a.bootstrap)
    ir=[r['intrinsic_minus_random'] for r in records]
    isp=[r['intrinsic_minus_spsa'] for r in records]
    ib=[r['intrinsic_minus_before'] for r in records]
    ciir=bootstrap_ci(ir,20260823,a.bootstrap)
    ciis=bootstrap_ci(isp,20260824,a.bootstrap)
    ciib=bootstrap_ci(ib,20260825,a.bootstrap)
    gradnorm=float(np.linalg.norm(tg));anis=float(np.max(np.abs(he))/max(np.min(np.abs(he[np.abs(he)>1e-12]),initial=np.inf),1e-12))
    diagnoses=[]
    if gradnorm<1e-4:diagnoses.append('TASK_GRADIENT_TOO_SMALL')
    if anis<3:diagnoses.append('TASK_LANDSCAPE_NEAR_ISOTROPIC')
    if pear>-0.25:diagnoses.append('GATE_TASK_MISALIGNMENT')
    if ciefr[0]<=0:diagnoses.append('GEOMETRIC_DIRECTION_NOT_ABOVE_RANDOM')
    if ciefs[0]<=0:diagnoses.append('GEOMETRIC_DIRECTION_NOT_ABOVE_SPSA')
    if cipi[0]>0:diagnoses.append('HESSIAN_PRECONDITIONING_ADDS_VALUE')
    if cipr[0]>0 and cips[0]>0:diagnoses.append('PRECONDITIONED_GEOMETRIC_DIRECTION_SUPPORTED')
    if ciir[0]>0 and ciis[0]>0:diagnoses.append('INTRINSIC_GEOMETRIC_ADVANTAGE_SUPPORTED')
    if not diagnoses:diagnoses=['GEOMETRIC_DIRECTION_SUPPORTED']
    checks={
      'exact_order_is_four':pow(A_BASE,ORDER,N)==1 and all(pow(A_BASE,k,N)!=1 for k in range(1,ORDER)),
      'ideal_exact_order_probability_is_half':abs(ideal_order_success()-.5)<1e-12,
      'response_rank_five_tangent_dim_four':np.linalg.matrix_rank(A)==5 and round(np.trace(P_T))==4,
      'three_way_budget_exact':max(gaps)==0,
      'seven_way_budget_exact':max(all_gaps)==0,
      'ideal_multiplier_preserved':max(r['hybrid_ideal_multiplier_change'] for r in records)<1e-10,
      'random_is_basis_invariant_tangent':max(r['random_normal_component'] for r in records)<1e-10,
      'online_normal_residual_controlled':max(r['final_hybrid_response_residual'] for r in records)<1e-10,
      'hybrid_improves_task_majority':np.mean([r['success_hybrid']>r['success_before'] for r in records])>=.75,
      'hybrid_beats_random_majority':np.mean(np.asarray(hr)>0)>=.75,
      'hybrid_beats_random_ci_positive':cihr[0]>0,
      'hybrid_beats_tangent_ci_positive':ciht[0]>0,
      'exact_flow_beats_random_ci_positive':ciefr[0]>0,
      'exact_flow_beats_spsa_ci_positive':ciefs[0]>0}
    checks.update({'preconditioned_beats_intrinsic_ci_positive':cipi[0]>0,
      'preconditioned_beats_random_ci_positive':cipr[0]>0,
      'preconditioned_beats_spsa_ci_positive':cips[0]>0})
    primary_checks={
      'exact_order_is_four':checks['exact_order_is_four'],
      'ideal_exact_order_probability_is_half':checks['ideal_exact_order_probability_is_half'],
      'response_rank_five_tangent_dim_four':checks['response_rank_five_tangent_dim_four'],
      'seven_way_budget_exact':checks['seven_way_budget_exact'],
      'ideal_multiplier_preserved':checks['ideal_multiplier_preserved'],
      'intrinsic_improves_over_reference_ci_positive':ciib[0]>0,
      'intrinsic_beats_basis_invariant_random_ci_positive':ciir[0]>0,
      'intrinsic_beats_spsa_ci_positive':ciis[0]>0,
      'intrinsic_beats_random_majority':np.mean(np.asarray(ir)>0)>=.75,
      'intrinsic_beats_spsa_majority':np.mean(np.asarray(isp)>0)>=.75}
    result={'scientific_status':'INTRINSIC_SHOR_TASK_FIBRE_ADVANTAGE_FREEZE_CANDIDATE',
      'boundary':'N=15,a=2 exact state-vector order-finding distribution with synthetic coherent/dephasing noise; not native gate hardware, fault tolerance, cryptographic scale, or asymptotic speedup.',
      'version':VERSION,'protocol':{'N':N,'a':A_BASE,'exact_order':ORDER,
       'control_qubits':CONTROL_QUBITS,'success_bins':SUCCESS_BINS,
       'ideal_exact_order_probability':ideal_order_success(),
       'success_definition':'measurement bin whose continued-fraction denominator equals exact order 4',
       'meta_seeds':a.meta_seeds,'train_per_meta':5,'shifted_heldout_per_meta':8,
       'steps':a.steps,'three_way_equal_budget':True,
       'landscape_samples':a.landscape_samples,
       'random':'v~N(0,I9); theta=r P_Tv/||P_Tv||; r=1.6u^(1/4)',
       'online_normal':'theta <- theta-beta J^dagger R(theta) after every drifted tangent step',
       'bootstrap_draws':a.bootstrap},
      'summary':{'mean_success_before':float(np.mean([r['success_before'] for r in records])),
       'mean_success_tangent':float(np.mean([r['success_tangent'] for r in records])),
       'mean_success_hybrid':float(np.mean([r['success_hybrid'] for r in records])),
       'mean_success_random':float(np.mean([r['success_basis_invariant_random'] for r in records])),
       'mean_success_exact_fibre_flow':float(np.mean([r['success_exact_fibre_flow'] for r in records])),
       'mean_success_exact_fibre_spsa':float(np.mean([r['success_exact_fibre_spsa'] for r in records])),
       'mean_success_intrinsic_euclidean':float(np.mean([r['success_intrinsic_euclidean'] for r in records])),
       'mean_success_hessian_preconditioned':float(np.mean([r['success_hessian_preconditioned'] for r in records])),
       'hybrid_vs_random_mean':float(np.mean(hr)),'hybrid_vs_random_bootstrap_95ci':cihr,
       'hybrid_vs_random_win_fraction':float(np.mean(np.asarray(hr)>0)),
       'hybrid_vs_random_sign_p_two_sided':sign_p(hr),
       'hybrid_vs_tangent_mean':float(np.mean(ht)),'hybrid_vs_tangent_bootstrap_95ci':ciht,
       'hybrid_vs_tangent_win_fraction':float(np.mean(np.asarray(ht)>0)),
       'exact_flow_vs_random_mean':float(np.mean(efr)),'exact_flow_vs_random_bootstrap_95ci':ciefr,
       'exact_flow_vs_spsa_mean':float(np.mean(efs)),'exact_flow_vs_spsa_bootstrap_95ci':ciefs,
       'preconditioned_vs_random_mean':float(np.mean(pr)),'preconditioned_vs_random_bootstrap_95ci':cipr,
       'preconditioned_vs_spsa_mean':float(np.mean(ps)),'preconditioned_vs_spsa_bootstrap_95ci':cips,
       'preconditioned_vs_intrinsic_mean':float(np.mean(pi)),'preconditioned_vs_intrinsic_bootstrap_95ci':cipi,
       'intrinsic_vs_reference_mean':float(np.mean(ib)),'intrinsic_vs_reference_bootstrap_95ci':ciib,
       'intrinsic_vs_random_mean':float(np.mean(ir)),'intrinsic_vs_random_bootstrap_95ci':ciir,
       'intrinsic_vs_random_win_fraction':float(np.mean(np.asarray(ir)>0)),
       'intrinsic_vs_random_sign_p_two_sided':sign_p(ir),
       'intrinsic_vs_spsa_mean':float(np.mean(isp)),'intrinsic_vs_spsa_bootstrap_95ci':ciis,
       'intrinsic_vs_spsa_win_fraction':float(np.mean(np.asarray(isp)>0)),
       'intrinsic_vs_spsa_sign_p_two_sided':sign_p(isp),
       'maximum_seven_way_budget_gap':int(max(all_gaps))},
      'mechanism_diagnostic':{'projected_task_gradient_norm_at_reference':gradnorm,
       'tangent_hessian_eigenvalues':he.tolist(),'tangent_hessian_abs_anisotropy':anis,
       'gate_proxy_vs_task_success_pearson':pear,'gate_proxy_vs_task_success_spearman':spear,
       'gate_task_direction_conflict_fraction':conflict,'classification':diagnoses},
      'records':records,'primary_checks':{k:bool(v) for k,v in primary_checks.items()},
      'exploratory_ablation_checks':{k:bool(v) for k,v in checks.items()},
      'all_primary_checks_pass':bool(all(primary_checks.values())),
      'interpretation':'Primary claim concerns intrinsic Euclidean fibre flow versus reference, basis-invariant random search, and SPSA. Hessian and drifted-flow outcomes are non-blocking ablations.'}
    with open(a.json_out,'w') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2));return 0 if result['all_primary_checks_pass'] else 2


if __name__=='__main__':
    c=main()
    if 'ipykernel' not in sys.modules and 'google.colab' not in sys.modules:raise SystemExit(c)

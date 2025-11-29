## Weird Behaviour

1. compiler in non-strict mode but not in strict mode

```
let crowbars = ( true as true )

const quatrains = ( true as boolean )

let miniature = ((crowbars) || (quatrains))

function blink(aqueous: string): -56 
{
  let photoed = ( -56 as -56 );
  const vectors = ( false as boolean );
  miniature = vectors;
  return  photoed;
}
```

Filed the issue (https://github.com/microsoft/TypeScript/issues/62814), the discussion from the developers seem to suggest that this is a valid behavior but we believe this isn't well documented.

2. Undocumented Keyof Behaviour

keyof (() => number) gives never

```
class Wezen {
  constructor(pyorrhea: number, quashed: string) {
    this.pyorrhea = pyorrhea
    this.quashed = quashed
  }
  pyorrhea: number

  quashed: string
  rhetoric(lactose: undefined, privates: number): number{
    return ((undefined as unknown) as keyof (() => number))
  }

  judaeo(relearned: number, detoured: (p0: null,p1: number) => keyof ((p0: boolean) => null)){
    return ( "ratio" as "ratio" )
  }
}
```

Smaller programs to reproduce the bugs
```
function fxxk(): number 
{
    return ( 42 as number );
}
let z = fxxk
type x = keyof (() => 10);

type y = keyof (typeof z)
```

and 

```
function fxxk(): number 
{
    return ( 42 as number );
}
let z: Object = fxxk
type x = keyof (() => 10);

type y = keyof (typeof z)
```

Seems to be related/similar to https://github.com/microsoft/TypeScript/issues/16578 .
Seems to be known already.

3. Not assignable bug (duplicate of https://github.com/microsoft/TypeScript/issues/31570)
Program : 1374
Bug: 

```
TS2416Property 'tweed' in type 'Willing' is not assignable to the same property in base type 'Carotids<63, 63>'.\nTS2416Property 'tweed' in type 'Campaign' is not assignable to the same property in base type 'Carnage<number, \"toString\" | \"valueOf\" | \"toLocaleString\" | \"toFixed\" | \"toExponential\" | \"toPrecision\">'.\nTS2416Property 'tweed' in type 'Develop<L, U>' is not assignable to the same property in base type 'Carotids<63, U>'.\nTS2416Property 'tweed' in type 'Upland' is not assignable to the same property in base type 'Carnage<63, Object>'.\nTS2416Property 'tweed' in type 'Onega<R, L, U>' is not assignable to the same property in base type 'Carotids<number, boolean>'.
```

Program
```ts
interface Carotids<P, A> {
  tweed<F_W extends number, F_R>(decimate: Carotids<number, number> | F_R | F_W | 63): Carotids<number, number> | F_R | F_W | 63
}

class Willing implements Carotids<integral, integral> {
  constructor() {
  }
  tweed<F_W extends number, F_R>(decimate: Carotids<number, number> | F_R | F_W | 63): Carotids<number, number> | F_R | F_W | 63 
{
    return 63;
    }

}
```



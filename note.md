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
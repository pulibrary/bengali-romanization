use rustfst::algorithms::rm_epsilon::rm_epsilon;
use rustfst::prelude::*;
use rustfst::{fst_impls::VectorFst, fst_traits::SerializableFst, semirings::TropicalWeight};

const RAW_FST: &[u8; 126462] = include_bytes!("../../TRANSLITERATOR");

fn main() {
    println!("This program will attempt to read the fst from disk");
    println!("If you want to run this, first compile a thrax grammar with `make`");
    println!("Then decompress the output .far file with farextract my-thrax.far");
    let fst = VectorFst::<TropicalWeight>::load(RAW_FST).unwrap();

    // If you install graphviz, then you can supposedly run: `cat chart.gv | dot -Tsvg > output.svg`
    // It just hangs forever for me though
    // fst.draw("chart.gv", &DrawingConfig::default()).unwrap();

    println!(
        "Loaded FST and it is great. Start state: {}",
        fst.start().unwrap()
    );

    let input_str = "masala";
    let input_bytes = input_str.as_bytes();
    let mut input_fst = VectorFst::<TropicalWeight>::new();

    let start_state = input_fst.add_state();
    input_fst.set_start(start_state).unwrap();

    let mut prev_state = start_state;
    for &sym in input_bytes.iter() {
        let next_state = input_fst.add_state();
        // Input label = sym, Output label = eps (0), weight = 1.0 (TropicalWeight::one())
        input_fst
            .add_tr(
                prev_state,
                Tr::new(sym as Label, 0, TropicalWeight::one(), next_state),
            )
            .unwrap();
        prev_state = next_state;
    }
    input_fst
        .set_final(prev_state, TropicalWeight::one())
        .unwrap();

    if let Some(st) = fst.input_symbols() {
        input_fst.set_input_symbols(st.clone());
    }

    let composed: VectorFst<TropicalWeight> =
        rustfst::algorithms::compose::compose(input_fst, fst).unwrap();
    println!("Composed FST has {} states", composed.num_states());

    let mut output_fst = composed.clone();
    rustfst::algorithms::project(&mut output_fst, ProjectType::ProjectOutput);

    rm_epsilon(&mut output_fst).unwrap();

    let shortest: VectorFst<TropicalWeight> = shortest_path(&output_fst).unwrap();

    shortest
        .string_paths_iter()
        .unwrap()
        .for_each(|s| println!("Hello we have a string path it is so nice, {s:?}"));
}

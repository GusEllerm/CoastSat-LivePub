vos_files = pd.Series(
    sorted(glob("shoreline_data_run6/*/time_series_tidally_corrected.csv"))
)
vos_files = vos_files[~vos_files.str.contains("nzd")]
vos_files
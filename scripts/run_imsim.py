import galsim
import desc.imsim

band = 'z'
stream = '000025'
visit = 32678

instcat = '/global/cscratch1/sd/descpho/Pipeline-tasks/DC2-R1-2p-WFD-{}/{}/instCat/phosim_cat_{}.txt'.format(band, stream, visit)

outdir = '/global/cscratch1/sd/jchiang8/imsim_pipeline/imSim/work/process_monitor_tests/{}band/v{}-{}'.format(band, visit, band)

commands = desc.imsim.metadata_from_file(instcat)

obs_md = desc.imsim.phosim_obs_metadata(commands)

rng = galsim.UniformDeviate(commands['seed'])
psf = desc.imsim.make_psf('Atmospheric', obs_md, rng=rng)

file_id = 'v{}-{}'.format(visit, band)

image_simulator = desc.imsim.ImageSimulator(instcat, psf,
                                            outdir=outdir,
                                            apply_sensor_model=True,
                                            file_id=file_id,
                                            log_level='INFO')
processes = 68
image_simulator.run(processes=processes)

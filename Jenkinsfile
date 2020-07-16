params = [:]
params.ROOT_COMPONENT = "atomspace";

println ("define components");

Code ocpkg = code("ocpkg").repo(params.OCPKG_REPO).branch(params.OCPKG_BRANCH);
Code atomspace_sql = code("atomspace_sql").repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH);

Docker opencog_deps = docker("opencog_deps").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
.requires(ocpkg);
Docker postgres = docker("postgres").repo(params.DOCKER_REPO).branch(params.DOCKER_BRANCH)
.requires(atomspace_sql);

Deb cogutil = deb("cogutil").repo(params.COGUTIL_REPO).branch(params.COGUTIL_BRANCH)
.requires(opencog_deps);
Deb atomspace = deb("atomspace").repo(params.ATOMSPACE_REPO).branch(params.ATOMSPACE_BRANCH)
.requires(opencog_deps, postgres, cogutil);
Deb cogserver = deb("cogserver").repo(params.COGSERVER_REPO).branch(params.COGSERVER_BRANCH)
.requires(opencog_deps, cogutil, atomspace);
Deb attention = deb("attention").repo(params.ATTENTION_REPO).branch(params.ATTENTION_BRANCH)
.requires(opencog_deps, cogutil, atomspace, cogserver);
Deb ure = deb("ure").repo(params.URE_REPO).branch(params.URE_BRANCH)
.requires(opencog_deps, cogutil, atomspace);
Deb pln = deb("pln").repo(params.PLN_REPO).branch(params.PLN_BRANCH)
.requires(opencog_deps, cogutil, atomspace, ure);
Deb opencog = deb("opencog").repo(params.OPENCOG_REPO).branch(params.OPENCOG_BRANCH)
.requires(opencog_deps, cogutil, atomspace, cogserver, attention, ure, pln);

println ("save dependencies");

deps = dependencies(ocpkg, atomspace_sql, opencog_deps, postgres,
    	cogutil, atomspace, cogserver, attention, ure, pln, opencog);

println ("get the list of stages and execute them");

for (String stage : deps.stagesFor(params.ROOT_COMPONENT)) {
    println ("stage: " + stage);
    //parallel stage
}

class Dependencies {

	private final Component[] components;

	public Dependencies(Component... components) {
		this.components = components;
	}

	// FIXME: what is correct type to return from this method?
	public List<String> stagesFor(String rootName) {
		List<String> stages = [];

		Component root  = componentByName(rootName);
		Set<Component> built = new HashSet<>(root.getRequirements());

		while (immediateStageFor(root, new HashSet<Component>(built), { stage, components ->
			stages.add(stage);
			built.addAll(components);
		}));

		return stages;
	}

	private Component componentByName(String name) {
		for (Component comp : components) {
			if (comp.getName().equals(name)) {
				return comp;
			}
		}
		throw new IllegalArgumentException("Could not find component name: " + name);
	}

	private boolean immediateStageFor(Component root, Set<Component> built, Closure<Boolean> callback) {
		String stage = null;
		Set<Component> stageComponents = new HashSet<>();

		for (Component comp : components) {
			if (built.contains(comp)) {
				continue;
			}
			// FIXME: how to apply root and noroot cases correctly
			if (comp.getRequirements().isEmpty() && root != null) {
				continue;
			}
			if (!built.containsAll(comp.getRequirements())) {
				continue;
			}

			stageComponents.add(comp);

			if (stage == null) {
				stage = "";
			}
			stage += comp.getName() + ", ";
		}

		if (stage == null) {
			return false;
		}

		callback.call(stage, stageComponents);
		return true;
	}

}

Dependencies dependencies(Component... components) {
	return new Dependencies(components);
}

interface Component {

	String getName();
	Set<Component> getRequirements();

}

abstract class Repo<T> {

	protected String repo;
	protected String branch;

	public T repo(String repo) {
		this.repo = repo;	
		return (T)this;
	}

	public T branch(String branch) {
		this.branch = branch;	
		return (T)this;
	}

	@Override
	public String toString() {
		return "Repo(repo: " + repo + ", branch: " + branch + ")";
	}

}

class Code extends Repo<Code> implements Component {

	private final String name;

	public Code(String name) {
		this.name = name;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public Set<Component> getRequirements() {
		return Collections.emptySet();
	}

}

Code code(String name) {
	return new Code(name);
}

abstract class Job<T> extends Repo<T> implements Component {

	protected String name;
	protected Set<Component> reqs = new HashSet<>();

	public Job(String name) {
		this.name = name;
	}

	public T requires(Component... reqs) {
		this.reqs.addAll(Arrays.asList(reqs));
		return (T)this;
	}

	@Override
	public String getName() {
		return name;
	}

	@Override
	public Set<Component> getRequirements() {
		return reqs;
	}

	@Override
	public String toString() {
		return "Job(name: " + name + ")";
	}

}

class Docker extends Job<Docker> {
	public Docker(String name) {
		super(name);
	}
}

Docker docker(String name) {
	return new Docker(name);
}

class Deb extends Job<Deb> {
	public Deb(String name) {
		super(name);
	}
}

Deb deb(String name) {
	return new Deb(name);
}

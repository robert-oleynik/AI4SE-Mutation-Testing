package de.hpi.ai4se.mutations;

/**
 * Hello world!
 *
 */
public class App 
{
	private int i;

	@Mutate
	public App() {
		this.i = 1;
	}

	@Mutate
	public int func() {
		return this.i;
	}

	@Mutate
	@Deprecated
	public int func2() {
		return this.i;
	}

	@Deprecated
	public void dep() {}

    public static void main( String[] args )
    {
        System.out.println( "Hello World!" );
		System.out.println(new App().i);
    }
}
